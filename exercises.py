"""Base de dados: músculos, equipamentos e exercícios."""
import re
import unicodedata

MUSCLES = {
    "peito": "Peito",
    "costas": "Costas",
    "trapezio": "Trapézio",
    "delt_ant": "Ombro (anterior)",
    "delt_lat": "Ombro (lateral)",
    "delt_post": "Ombro (posterior)",
    "biceps": "Bíceps",
    "triceps": "Tríceps",
    "antebraco": "Antebraço",
    "quadriceps": "Quadríceps",
    "posterior": "Posterior de coxa",
    "gluteos": "Glúteos",
    "adutores": "Adutores",
    "panturrilha": "Panturrilha",
    "abdomen": "Abdômen",
    "lombar": "Lombar",
}

# Grupos de equipamentos exibidos em "Minha Academia"
EQUIPMENT_GROUPS = [
    ("Pesos livres", [
        ("barra", "Barra reta e anilhas"),
        ("barra_w", "Barra W (EZ)"),
        ("halteres", "Halteres"),
        ("banco", "Banco reto / ajustável"),
        ("rack", "Rack / gaiola de agachamento"),
        ("smith", "Smith (barra guiada)"),
        ("scott", "Banco Scott"),
    ]),
    ("Cabos e peso corporal", [
        ("polia", "Crossover / polia ajustável"),
        ("puxador", "Puxador alto (pulley)"),
        ("remada_baixa", "Remada baixa (polia sentada)"),
        ("barra_fixa", "Barra fixa"),
        ("paralelas", "Paralelas"),
        ("graviton", "Gráviton (barra/paralela assistida)"),
        ("banco_romano", "Banco romano (hiperextensão 45°)"),
    ]),
    ("Máquinas de peito e ombro", [
        ("supino_maq", "Supino máquina (chest press)"),
        ("supino_incl_maq", "Supino inclinado máquina"),
        ("peck_deck", "Peck deck / voador"),
        ("desenv_maq", "Desenvolvimento máquina"),
        ("lateral_maq", "Elevação lateral máquina"),
    ]),
    ("Máquinas de costas", [
        ("puxada_maq", "Puxada articulada (máquina)"),
        ("remada_maq", "Remada máquina (peito apoiado)"),
        ("remada_t", "Remada cavalinho (T-bar)"),
        ("pullover_maq", "Pullover máquina"),
    ]),
    ("Máquinas de braço e abdômen", [
        ("biceps_maq", "Rosca Scott máquina"),
        ("triceps_maq", "Tríceps máquina"),
        ("abdominal_maq", "Abdominal máquina"),
    ]),
    ("Máquinas de perna", [
        ("leg_press", "Leg press 45°"),
        ("leg_press_h", "Leg press horizontal"),
        ("hack", "Hack machine"),
        ("pendulo", "Agachamento pêndulo"),
        ("extensora", "Cadeira extensora"),
        ("flexora_deitada", "Mesa flexora (deitado)"),
        ("flexora_sentada", "Cadeira flexora (sentado)"),
        ("flexora_pe", "Flexora em pé"),
        ("adutora", "Cadeira adutora"),
        ("abdutora", "Cadeira abdutora"),
        ("gluteo_maq", "Glúteo máquina (coice)"),
        ("hip_thrust_maq", "Elevação pélvica máquina"),
        ("pant_pe", "Panturrilha em pé máquina"),
        ("pant_sentado", "Panturrilha sentado máquina"),
    ]),
]

ALL_EQUIPMENT = [k for _, items in EQUIPMENT_GROUPS for k, _ in items]

PRESETS = {
    "completa": {"nome": "Academia completa", "itens": ALL_EQUIPMENT},
    "basica": {"nome": "Academia básica", "itens": [
        "barra", "barra_w", "halteres", "banco", "rack", "smith", "scott", "polia",
        "puxador", "remada_baixa", "barra_fixa", "paralelas", "peck_deck", "leg_press",
        "extensora", "flexora_deitada", "adutora", "abdutora", "pant_pe",
    ]},
    "casa": {"nome": "Em casa (halteres)", "itens": ["halteres", "banco", "barra_fixa"]},
}

PATTERNS = {
    "push_h": "Supino horizontal", "push_incl": "Supino inclinado", "fly": "Crucifixo",
    "dip": "Mergulho", "push_v": "Desenvolvimento", "lat_raise": "Elevação lateral",
    "front_raise": "Elevação frontal", "rear_delt": "Deltoide posterior",
    "pull_v": "Puxada vertical", "pull_h": "Remada", "pullover": "Pullover",
    "shrug": "Encolhimento", "curl": "Rosca", "hammer": "Rosca martelo",
    "tri_push": "Tríceps na polia", "tri_overhead": "Tríceps acima da cabeça",
    "tri_compound": "Tríceps composto", "wrist": "Antebraço", "squat": "Agachamento",
    "lunge": "Unilateral de perna", "leg_ext": "Extensão de joelho",
    "hinge": "Levantamento (quadril)", "leg_curl": "Flexão de joelho",
    "hip_thrust": "Elevação pélvica", "glute_iso": "Glúteo isolado",
    "abduction": "Abdução", "adduction": "Adução", "calf": "Panturrilha em pé",
    "calf_seated": "Panturrilha sentado", "abs_flex": "Flexão de tronco",
    "abs_leg": "Elevação de pernas", "abs_stab": "Estabilização", "back_ext": "Extensão lombar",
}

# nome | primário | secundários | equipamentos | C/I | padrão | nível (1-3) | alongado (0/1)
_RAW = """
Supino reto com barra|peito|delt_ant triceps|barra banco|C|push_h|3|0
Supino reto com halteres|peito|delt_ant triceps|halteres banco|C|push_h|3|1
Supino reto no Smith|peito|delt_ant triceps|smith banco|C|push_h|2|0
Supino máquina (chest press)|peito|delt_ant triceps|supino_maq|C|push_h|3|0
Supino declinado com barra|peito|delt_ant triceps|barra banco|C|push_h|2|0
Flexão de braço|peito|delt_ant triceps||C|push_h|1|0
Supino inclinado com barra|peito|delt_ant triceps|barra banco|C|push_incl|3|0
Supino inclinado com halteres|peito|delt_ant triceps|halteres banco|C|push_incl|3|1
Supino inclinado no Smith|peito|delt_ant triceps|smith banco|C|push_incl|3|0
Supino inclinado máquina|peito|delt_ant triceps|supino_incl_maq|C|push_incl|3|0
Mergulho nas paralelas (foco peito)|peito|triceps delt_ant|paralelas|C|dip|3|1
Mergulho assistido no gráviton|peito|triceps delt_ant|graviton|C|dip|2|1
Crucifixo no peck deck (voador)|peito|delt_ant|peck_deck|I|fly|3|1
Crossover na polia|peito|delt_ant|polia|I|fly|3|1
Crucifixo na polia baixa (de baixo para cima)|peito|delt_ant|polia|I|fly|2|0
Crucifixo com halteres|peito|delt_ant|halteres banco|I|fly|2|1
Crucifixo inclinado com halteres|peito|delt_ant|halteres banco|I|fly|2|1
Barra fixa pronada|costas|biceps antebraco|barra_fixa|C|pull_v|3|1
Barra fixa supinada (chin-up)|costas|biceps|barra_fixa|C|pull_v|3|1
Barra fixa assistida (gráviton)|costas|biceps|graviton|C|pull_v|2|1
Puxada alta pegada aberta|costas|biceps|puxador|C|pull_v|3|1
Puxada alta com triângulo (neutra)|costas|biceps|puxador|C|pull_v|3|1
Puxada alta supinada|costas|biceps|puxador|C|pull_v|2|1
Puxada unilateral na polia|costas|biceps|polia|C|pull_v|3|1
Puxada articulada (máquina)|costas|biceps|puxada_maq|C|pull_v|3|0
Remada curvada com barra|costas|biceps delt_post lombar|barra|C|pull_h|3|0
Remada cavalinho (T-bar)|costas|biceps delt_post trapezio|remada_t|C|pull_h|3|0
Remada baixa com triângulo|costas|biceps delt_post|remada_baixa|C|pull_h|3|1
Remada baixa pegada aberta|costas|delt_post trapezio biceps|remada_baixa|C|pull_h|3|0
Remada máquina (peito apoiado)|costas|biceps delt_post trapezio|remada_maq|C|pull_h|3|0
Remada unilateral com halter (serrote)|costas|biceps delt_post|halteres banco|C|pull_h|3|1
Remada com halteres no banco inclinado|costas|biceps delt_post trapezio|halteres banco|C|pull_h|3|0
Remada unilateral na polia|costas|biceps delt_post|polia|C|pull_h|2|1
Remada no Smith|costas|biceps delt_post|smith|C|pull_h|1|0
Remada invertida na barra|costas|biceps delt_post|smith|C|pull_h|1|0
Pullover na polia (braços estendidos)|costas|triceps|polia|I|pullover|2|1
Pullover máquina|costas|triceps|pullover_maq|I|pullover|3|1
Pullover com halter|costas|peito triceps|halteres banco|I|pullover|1|1
Encolhimento com halteres|trapezio|antebraco|halteres|I|shrug|3|0
Encolhimento com barra|trapezio|antebraco|barra|I|shrug|2|0
Encolhimento no Smith|trapezio|antebraco|smith|I|shrug|2|0
Encolhimento na polia|trapezio|antebraco|polia|I|shrug|2|0
Desenvolvimento com halteres|delt_ant|delt_lat triceps|halteres banco|C|push_v|3|0
Desenvolvimento máquina|delt_ant|delt_lat triceps|desenv_maq|C|push_v|3|0
Desenvolvimento militar com barra|delt_ant|delt_lat triceps|barra|C|push_v|2|0
Desenvolvimento no Smith|delt_ant|delt_lat triceps|smith banco|C|push_v|2|0
Desenvolvimento Arnold|delt_ant|delt_lat triceps|halteres banco|C|push_v|2|0
Elevação lateral na polia|delt_lat||polia|I|lat_raise|3|1
Elevação lateral máquina|delt_lat||lateral_maq|I|lat_raise|3|0
Elevação lateral com halteres|delt_lat||halteres|I|lat_raise|2|0
Elevação lateral deitado no banco inclinado|delt_lat||halteres banco|I|lat_raise|2|1
Elevação frontal com halteres|delt_ant||halteres|I|front_raise|1|0
Elevação frontal na polia|delt_ant||polia|I|front_raise|1|0
Crucifixo inverso no peck deck|delt_post|trapezio|peck_deck|I|rear_delt|3|0
Crucifixo inverso na polia|delt_post|trapezio|polia|I|rear_delt|3|1
Crucifixo inverso com halteres|delt_post|trapezio|halteres|I|rear_delt|2|0
Face pull|delt_post|trapezio|polia|I|rear_delt|2|0
Rosca inclinada com halteres|biceps|antebraco|halteres banco|I|curl|3|1
Rosca bayesian na polia (de costas)|biceps|antebraco|polia|I|curl|3|1
Rosca Scott com barra W|biceps|antebraco|scott barra_w|I|curl|3|1
Rosca Scott com halter (unilateral)|biceps|antebraco|scott halteres|I|curl|3|1
Rosca Scott máquina|biceps|antebraco|biceps_maq|I|curl|3|1
Rosca direta com barra W|biceps|antebraco|barra_w|I|curl|2|0
Rosca direta com barra|biceps|antebraco|barra|I|curl|2|0
Rosca alternada com halteres|biceps|antebraco|halteres|I|curl|2|0
Rosca na polia baixa|biceps|antebraco|polia|I|curl|2|0
Rosca concentrada|biceps||halteres|I|curl|2|0
Rosca martelo com halteres|biceps|antebraco|halteres|I|hammer|2|0
Rosca martelo na polia (corda)|biceps|antebraco|polia|I|hammer|2|0
Tríceps francês na polia (acima da cabeça)|triceps||polia|I|tri_overhead|3|1
Tríceps testa com barra W|triceps||barra_w banco|I|tri_overhead|3|1
Tríceps testa com halteres|triceps||halteres banco|I|tri_overhead|2|1
Tríceps francês com halter|triceps||halteres|I|tri_overhead|2|1
Tríceps na polia com barra|triceps||polia|I|tri_push|2|0
Tríceps na polia com corda|triceps||polia|I|tri_push|2|0
Tríceps unilateral na polia|triceps||polia|I|tri_push|2|0
Tríceps na polia alta do puxador|triceps||puxador|I|tri_push|2|0
Tríceps máquina|triceps||triceps_maq|I|tri_push|2|0
Tríceps coice com halter|triceps||halteres|I|tri_push|1|0
Supino fechado|triceps|peito delt_ant|barra banco|C|tri_compound|2|0
Paralelas (foco tríceps)|triceps|peito delt_ant|paralelas|C|tri_compound|2|1
Mergulho no banco|triceps|delt_ant|banco|C|tri_compound|1|0
Flexão diamante|triceps|peito delt_ant||C|tri_compound|1|0
Rosca inversa com barra W|antebraco|biceps|barra_w|I|wrist|2|0
Rosca de punho com barra|antebraco||barra|I|wrist|2|0
Rosca de punho com halteres|antebraco||halteres|I|wrist|2|0
Rosca inversa na polia|antebraco|biceps|polia|I|wrist|2|0
Agachamento livre com barra|quadriceps|gluteos adutores lombar|barra rack|C|squat|3|1
Agachamento hack|quadriceps|gluteos adutores|hack|C|squat|3|1
Agachamento pêndulo|quadriceps|gluteos adutores|pendulo|C|squat|3|1
Leg press 45°|quadriceps|gluteos adutores|leg_press|C|squat|3|1
Agachamento no Smith|quadriceps|gluteos adutores|smith|C|squat|3|1
Agachamento frontal|quadriceps|gluteos lombar|barra rack|C|squat|2|1
Leg press horizontal|quadriceps|gluteos adutores|leg_press_h|C|squat|2|0
Agachamento goblet|quadriceps|gluteos adutores|halteres|C|squat|1|1
Agachamento livre (peso corporal)|quadriceps|gluteos||C|squat|1|0
Agachamento búlgaro|quadriceps|gluteos adutores|halteres banco|C|lunge|3|1
Afundo / passada com halteres|quadriceps|gluteos adutores|halteres|C|lunge|2|1
Afundo no Smith|quadriceps|gluteos adutores|smith|C|lunge|2|1
Step-up no banco|quadriceps|gluteos|halteres banco|C|lunge|1|0
Cadeira extensora|quadriceps||extensora|I|leg_ext|3|0
Agachamento sissy|quadriceps|||I|leg_ext|1|1
Levantamento terra romeno com barra (stiff)|posterior|gluteos lombar|barra|C|hinge|3|1
Levantamento terra romeno com halteres|posterior|gluteos lombar|halteres|C|hinge|3|1
Stiff no Smith|posterior|gluteos lombar|smith|C|hinge|2|1
Levantamento terra convencional|posterior|gluteos lombar costas trapezio|barra|C|hinge|2|0
Bom dia (good morning)|posterior|gluteos lombar|barra rack|C|hinge|2|1
Cadeira flexora (sentado)|posterior||flexora_sentada|I|leg_curl|3|1
Mesa flexora (deitado)|posterior||flexora_deitada|I|leg_curl|2|0
Flexora em pé (unilateral)|posterior||flexora_pe|I|leg_curl|2|0
Flexão nórdica|posterior|||I|leg_curl|2|1
Elevação pélvica com barra (hip thrust)|gluteos|posterior|barra banco|C|hip_thrust|3|0
Elevação pélvica máquina|gluteos|posterior|hip_thrust_maq|C|hip_thrust|3|0
Elevação pélvica no Smith|gluteos|posterior|smith banco|C|hip_thrust|2|0
Ponte de glúteo unilateral|gluteos|posterior||C|hip_thrust|1|0
Coice de glúteo na polia|gluteos||polia|I|glute_iso|2|0
Glúteo máquina (coice)|gluteos||gluteo_maq|I|glute_iso|2|0
Cadeira abdutora|gluteos||abdutora|I|abduction|2|0
Abdução de quadril na polia|gluteos||polia|I|abduction|1|0
Cadeira adutora|adutores||adutora|I|adduction|3|1
Adução de quadril na polia|adutores||polia|I|adduction|1|0
Panturrilha em pé máquina|panturrilha||pant_pe|I|calf|3|1
Panturrilha no leg press|panturrilha||leg_press|I|calf|3|1
Panturrilha no hack|panturrilha||hack|I|calf|2|1
Panturrilha no Smith (no degrau)|panturrilha||smith|I|calf|2|1
Panturrilha unilateral com halter (no degrau)|panturrilha||halteres|I|calf|2|1
Panturrilha em pé (peso corporal, no degrau)|panturrilha|||I|calf|1|1
Panturrilha sentado máquina|panturrilha||pant_sentado|I|calf_seated|2|1
Abdominal na polia (ajoelhado)|abdomen||polia|I|abs_flex|3|0
Abdominal máquina|abdomen||abdominal_maq|I|abs_flex|3|0
Abdominal supra no solo|abdomen|||I|abs_flex|1|0
Elevação de pernas na barra fixa|abdomen||barra_fixa|I|abs_leg|3|0
Elevação de joelhos nas paralelas|abdomen||paralelas|I|abs_leg|2|0
Elevação de pernas deitado|abdomen|||I|abs_leg|1|0
Prancha|abdomen|lombar||I|abs_stab|1|0
Hiperextensão 45° (banco romano)|lombar|gluteos posterior|banco_romano|I|back_ext|3|1
Superman no solo|lombar|gluteos||I|back_ext|1|0
"""


def _slug(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _load():
    out = []
    for line in _RAW.strip().splitlines():
        nome, prim, sec, equip, tipo, padrao, nivel, along = line.split("|")
        out.append({
            "id": _slug(nome),
            "nome": nome,
            "musculo": prim,
            "secundarios": sec.split(),
            "equip": equip.split(),
            "composto": tipo == "C",
            "padrao": padrao,
            "nivel": int(nivel),
            "alongado": along == "1",
        })
    return out


EXERCISES = _load()
BY_ID = {e["id"]: e for e in EXERCISES}
assert len(BY_ID) == len(EXERCISES), "ids de exercício duplicados"
