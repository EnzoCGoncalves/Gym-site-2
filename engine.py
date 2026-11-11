"""Motor de treino: gerador e avaliador.

Baseado nos consensos atuais de hipertrofia: volume semanal por músculo
(séries difíceis), frequência de ~2x/semana, séries perto da falha, descanso
adequado, exercícios estáveis e com tensão na posição alongada, e sessões que
caibam no tempo disponível.
"""
import re

from exercises import BY_ID, EXERCISES, MUSCLES

HEAVY = {"squat", "hinge", "push_h", "push_incl"}
MEDIUM = {"pull_v", "pull_h", "push_v", "dip", "lunge", "hip_thrust", "tri_compound"}
LIGHT = {"lat_raise", "rear_delt", "front_raise", "calf", "calf_seated",
         "abs_flex", "abs_leg", "abs_stab", "wrist", "back_ext"}
PUSH = {"push_h", "push_incl", "dip", "push_v", "fly"}
PULL = {"pull_v", "pull_h", "pullover", "rear_delt"}

NIVEIS = ("iniciante", "intermediario", "avancado")
OBJETIVOS = ("hipertrofia", "forca", "definicao")

_MAJOR = {"peito", "costas", "quadriceps", "posterior", "delt_lat", "biceps", "triceps"}
_MEDIUM = {"gluteos", "panturrilha", "delt_post"}


def faixa(musculo, nivel):
    """Faixa recomendada de séries semanais (mín, máx) para o músculo."""
    i = NIVEIS.index(nivel)
    if musculo in _MAJOR:
        return [(6, 12), (10, 20), (12, 24)][i]
    if musculo in _MEDIUM:
        return [(4, 12), (6, 16), (8, 20)][i]
    if musculo == "delt_ant":
        return [(3, 12), (4, 14), (4, 16)][i]
    return [(0, 12), (0, 16), (0, 20)][i]


def prescricao(ex, nivel, objetivo):
    """Repetições e descanso (s) recomendados para o exercício."""
    p = ex["padrao"]
    if p == "abs_stab":
        return "30-60s", 60
    if p in HEAVY:
        if objetivo == "forca":
            return "4-6", 210
        return ("8-12" if nivel == "iniciante" else "6-10"), 150
    if p in MEDIUM:
        return ("6-10", 150) if objetivo == "forca" else ("8-12", 120)
    if p in LIGHT:
        return ("12-20" if p in ("lat_raise", "rear_delt") else "10-15"), 60
    return "10-15", 75


def _reps_info(reps):
    s = str(reps).lower().strip()
    nums = [int(n) for n in re.findall(r"\d+", s)][:2]
    if not nums:
        return 10.0, False
    return sum(nums) / len(nums), s.endswith("s")


def tempo_exercicio(ex, series, reps, descanso):
    """Tempo estimado em segundos (execução + descansos + aquecimento + troca)."""
    media, segundos = _reps_info(reps)
    trabalho = media if segundos else media * 4
    trabalho = max(15, min(90, trabalho))
    aquec = 150 if ex["padrao"] in HEAVY else (60 if ex["composto"] else 0)
    return series * trabalho + max(0, series - 1) * descanso + 120 + aquec


def tempo_dia(itens):
    """Minutos estimados da sessão (inclui 5 min de aquecimento geral)."""
    if not itens:
        return 0
    total = 300
    for it in itens:
        ex = BY_ID.get(it["id"])
        if ex:
            total += tempo_exercicio(ex, it["series"], it["reps"], it["descanso"])
    return round(total / 60)


def _volume_dia(itens):
    vol = {}
    for it in itens:
        ex = BY_ID.get(it["id"])
        if not ex:
            continue
        vol[ex["musculo"]] = vol.get(ex["musculo"], 0) + it["series"]
        for s in ex["secundarios"]:
            vol[s] = vol.get(s, 0) + it["series"] * 0.5
    return vol


def _volume_semana(dias):
    total = {}
    for d in dias:
        for m, v in _volume_dia(d["exercicios"]).items():
            total[m] = total.get(m, 0) + v
    return total


# ----------------------------------------------------------------- gerador

SLOTS = {
    "peito_h": ("peito", ["push_h", "push_incl", "dip"]),
    "peito_incl": ("peito", ["push_incl", "push_h", "dip"]),
    "peito_fly": ("peito", ["fly", "dip"]),
    "costas_v": ("costas", ["pull_v"]),
    "costas_h": ("costas", ["pull_h"]),
    "pullover": ("costas", ["pullover", "pull_v"]),
    "ombro": ("delt_ant", ["push_v"]),
    "lateral": ("delt_lat", ["lat_raise"]),
    "delt_post": ("delt_post", ["rear_delt"]),
    "biceps": ("biceps", ["curl"]),
    "biceps2": ("biceps", ["hammer", "curl"]),
    "triceps": ("triceps", ["tri_overhead", "tri_push"]),
    "triceps2": ("triceps", ["tri_push", "tri_compound"]),
    "quad": ("quadriceps", ["squat"]),
    "uni": ("quadriceps", ["lunge", "squat"]),
    "ext": ("quadriceps", ["leg_ext"]),
    "hinge": ("posterior", ["hinge"]),
    "flexora": ("posterior", ["leg_curl"]),
    "gluteo": ("gluteos", ["hip_thrust", "glute_iso", "abduction"]),
    "adutor": ("adutores", ["adduction"]),
    "pant": ("panturrilha", ["calf", "calf_seated"]),
    "abs": ("abdomen", ["abs_flex", "abs_leg"]),
    "trap": ("trapezio", ["shrug"]),
}

# (slot, prioridade): 1 = essencial, 2 = importante, 3 = opcional
T = {
    "Full Body A": [("quad", 1), ("peito_h", 1), ("costas_v", 1), ("flexora", 1), ("lateral", 2),
                    ("triceps", 2), ("biceps", 2), ("pant", 3), ("abs", 3)],
    "Full Body B": [("hinge", 1), ("peito_incl", 1), ("costas_h", 1), ("uni", 1), ("ombro", 2),
                    ("biceps", 2), ("triceps", 2), ("pant", 3), ("abs", 3)],
    "Full Body C": [("quad", 1), ("costas_v", 1), ("peito_h", 1), ("flexora", 1), ("lateral", 2),
                    ("delt_post", 2), ("biceps", 3), ("triceps", 3), ("abs", 3)],
    "Superior A": [("peito_h", 1), ("costas_h", 1), ("ombro", 2), ("costas_v", 1), ("lateral", 1),
                   ("triceps", 2), ("biceps", 2), ("delt_post", 3)],
    "Superior B": [("costas_v", 1), ("peito_incl", 1), ("costas_h", 1), ("peito_fly", 2),
                   ("lateral", 1), ("biceps", 2), ("triceps", 2), ("delt_post", 2)],
    "Inferior A": [("quad", 1), ("hinge", 1), ("ext", 2), ("flexora", 1), ("pant", 2),
                   ("abs", 3), ("adutor", 3)],
    "Inferior B": [("quad", 1), ("flexora", 1), ("uni", 2), ("gluteo", 2), ("ext", 2),
                   ("pant", 2), ("abs", 3)],
    "Push (Empurrar)": [("peito_h", 1), ("peito_incl", 1), ("ombro", 2), ("lateral", 1),
                        ("triceps", 1), ("peito_fly", 3), ("triceps2", 2)],
    "Pull (Puxar)": [("costas_v", 1), ("costas_h", 1), ("delt_post", 2), ("biceps", 1),
                     ("biceps2", 2), ("pullover", 3), ("trap", 3)],
    "Legs (Pernas)": [("quad", 1), ("hinge", 1), ("uni", 2), ("flexora", 1), ("ext", 2),
                      ("pant", 1), ("abs", 3), ("adutor", 3)],
    "Push B": [("peito_incl", 1), ("ombro", 1), ("peito_fly", 1), ("lateral", 1),
               ("triceps", 1), ("triceps2", 2)],
    "Pull B": [("costas_h", 1), ("costas_v", 1), ("delt_post", 1), ("biceps", 1),
               ("biceps2", 2), ("pullover", 3)],
    "Legs B": [("hinge", 1), ("quad", 1), ("flexora", 1), ("uni", 2), ("gluteo", 2),
               ("pant", 1), ("abs", 3)],
}

SPLITS = {
    2: (["Full Body A", "Full Body B"], "Segunda e quinta"),
    3: (["Full Body A", "Full Body B", "Full Body C"], "Segunda, quarta e sexta"),
    4: (["Superior A", "Inferior A", "Superior B", "Inferior B"], "Segunda, terça, quinta e sexta"),
    5: (["Superior A", "Inferior A", "Push (Empurrar)", "Pull (Puxar)", "Legs B"],
        "Segunda, terça, quinta, sexta e sábado"),
    6: (["Push (Empurrar)", "Pull (Puxar)", "Legs (Pernas)", "Push B", "Pull B", "Legs B"],
        "Segunda a sábado"),
}


def _escolher(slot, disponiveis, usados_semana, usados_dia, nivel):
    musculo, padroes = SLOTS[slot]
    cands = [e for e in disponiveis if e["musculo"] == musculo and e["id"] not in usados_dia]
    do_padrao = [e for e in cands if e["padrao"] in padroes]
    pool = do_padrao or cands
    if not pool:
        return None

    def nota(e):
        idx = padroes.index(e["padrao"]) if e["padrao"] in padroes else len(padroes)
        n = e["nivel"] * 10 - idx * 4 + (2 if e["alongado"] else 0)
        if e["id"] in usados_semana:
            n -= 7
        if nivel == "iniciante" and not {"barra", "rack"} & set(e["equip"]):
            n += 3  # iniciantes: priorizar exercícios mais estáveis
        return n

    return max(pool, key=lambda e: (nota(e), e["nome"]))


def gerar(params):
    nivel = params.get("nivel") if params.get("nivel") in NIVEIS else "intermediario"
    objetivo = params.get("objetivo") if params.get("objetivo") in OBJETIVOS else "hipertrofia"
    try:
        n_dias = min(6, max(2, int(params.get("dias", 4))))
        tempo = min(120, max(25, int(params.get("tempo", 60))))
    except (TypeError, ValueError):
        n_dias, tempo = 4, 60
    prioridades = [m for m in params.get("prioridades", []) if m in MUSCLES][:3]
    equip = set(params.get("equip", []))
    disponiveis = [e for e in EXERCISES if set(e["equip"]) <= equip]

    nomes, agenda = SPLITS[n_dias]
    base = 2 if nivel == "iniciante" else 3
    teto_series = 3 if nivel == "iniciante" else 4
    avisos, faltando, usados_semana, dias = [], set(), set(), []

    for nome in nomes:
        usados_dia, itens = set(), []
        for slot, prio in T[nome]:
            ex = _escolher(slot, disponiveis, usados_semana, usados_dia, nivel)
            if not ex:
                faltando.add(MUSCLES[SLOTS[slot][0]])
                continue
            usados_dia.add(ex["id"])
            reps, descanso = prescricao(ex, nivel, objetivo)
            if ex["musculo"] in prioridades:
                prio = 1
            itens.append({"id": ex["id"], "series": base, "reps": reps,
                          "descanso": descanso, "_prio": prio})
        usados_semana |= usados_dia

        # Ajuste ao tempo disponível: corta o opcional antes do essencial
        while tempo_dia(itens) > tempo:
            p3 = [i for i in itens if i["_prio"] == 3]
            reduz = [i for i in itens if i["series"] > 2]
            p2 = [i for i in itens if i["_prio"] == 2]
            if p3:
                itens.remove(p3[-1])
            elif reduz:
                max(reversed(reduz), key=lambda i: i["series"])["series"] -= 1
            elif p2:
                itens.remove(p2[-1])
            elif len(itens) > 3:
                itens.pop()
            else:
                avisos.append(f"O tempo de {tempo} min é curto demais para o treino "
                              f"\"{nome}\"; ele ficou no mínimo possível.")
                break
        dias.append({"nome": nome, "exercicios": itens})

    # Preenche o tempo que sobrou com séries extras, sem passar do volume ideal
    def alvo(m):
        lo, hi = faixa(m, nivel)
        a = lo + (hi - lo) * 0.6
        if objetivo == "definicao":
            a *= 0.85
        return a + (3 if m in prioridades else 0)

    for _ in range(2):
        for prio in (1, 2, 3):
            for d in dias:
                for it in d["exercicios"]:
                    if it["_prio"] != prio or it["series"] >= teto_series:
                        continue
                    m = BY_ID[it["id"]]["musculo"]
                    if _volume_semana(dias).get(m, 0) + 1 > alvo(m):
                        continue
                    it["series"] += 1
                    if tempo_dia(d["exercicios"]) > tempo:
                        it["series"] -= 1

    for d in dias:
        for it in d["exercicios"]:
            it.pop("_prio")

    if faltando:
        avisos.append("Sem equipamento disponível para: " + ", ".join(sorted(faltando)) +
                      ". Marque mais equipamentos em \"Minha academia\" ou adicione exercícios manualmente.")
    if objetivo == "definicao":
        avisos.append("Em definição o treino continua pesado para preservar massa magra; "
                      "o déficit calórico vem da dieta. O volume foi levemente reduzido para "
                      "facilitar a recuperação.")
    rot = {"hipertrofia": "Hipertrofia", "forca": "Força + Hipertrofia", "definicao": "Definição"}
    return {
        "nome": f"{rot[objetivo]} {n_dias}x por semana",
        "nivel": nivel,
        "objetivo": objetivo,
        "agenda": agenda,
        "dias": dias,
        "avisos": avisos,
    }


# ---------------------------------------------------------------- avaliador

def normalizar(plano):
    """Limpa um plano vindo do cliente."""
    nivel = plano.get("nivel") if plano.get("nivel") in NIVEIS else "intermediario"
    objetivo = plano.get("objetivo") if plano.get("objetivo") in OBJETIVOS else "hipertrofia"
    dias = []
    for d in (plano.get("dias") or [])[:7]:
        itens = []
        for it in (d.get("exercicios") or [])[:25]:
            if it.get("id") not in BY_ID:
                continue
            try:
                series = min(10, max(1, int(it.get("series", 3))))
                descanso = min(600, max(15, int(it.get("descanso", 90))))
            except (TypeError, ValueError):
                series, descanso = 3, 90
            itens.append({"id": it["id"], "series": series,
                          "reps": str(it.get("reps", "8-12"))[:12], "descanso": descanso})
        dias.append({"nome": str(d.get("nome", "Treino"))[:40], "exercicios": itens})
    return {"nome": str(plano.get("nome", "Meu treino"))[:60], "nivel": nivel,
            "objetivo": objetivo, "agenda": str(plano.get("agenda", ""))[:80], "dias": dias}


def _conceito(nota):
    for corte, nome in ((90, "Elite"), (80, "Excelente"), (65, "Bom"), (50, "Regular")):
        if nota >= corte:
            return nome
    return "Precisa melhorar"


def avaliar(plano):
    plano = normalizar(plano)
    nivel = plano["nivel"]
    dias = [d for d in plano["dias"] if d["exercicios"]]
    info_dias = [{"nome": d["nome"], "minutos": tempo_dia(d["exercicios"]),
                  "series": sum(i["series"] for i in d["exercicios"]),
                  "exercicios": len(d["exercicios"])} for d in plano["dias"]]
    if not dias:
        return {"vazio": True, "nota": 0, "conceito": "—", "criterios": [], "volume": [],
                "dias": info_dias, "mensagens": [
                    {"tipo": "dica", "texto": "Adicione exercícios para receber a avaliação."}]}

    msgs = []

    def msg(tipo, texto):
        msgs.append({"tipo": tipo, "texto": texto})

    semana = _volume_semana(dias)
    por_dia = [_volume_dia(d["exercicios"]) for d in dias]

    # 1) Volume semanal ------------------------------------------------------
    volume, notas_vol, notas_freq = [], [], []
    baixos, altos, freq_baixa = [], [], []
    for m, nome in MUSCLES.items():
        lo, hi = faixa(m, nivel)
        s = semana.get(m, 0)
        freq = sum(1 for v in por_dia if v.get(m, 0) >= 1.5)
        if s < lo:
            status, n = "baixo", s / lo
            baixos.append(f"{nome} ({s:g} de {lo}–{hi})")
        elif s > hi:
            status, n = "alto", max(0.5, 1 - (s - hi) / hi)
            altos.append(f"{nome} ({s:g}, máx. {hi})")
        else:
            status, n = "ok", 1
        if lo > 0:
            notas_vol.append(n)
            if m != "delt_ant":
                notas_freq.append(1 if freq >= 2 else 0.55 if freq == 1 else 0)
                if freq == 1 and s >= lo * 0.5:
                    freq_baixa.append(nome)
        volume.append({"id": m, "nome": nome, "series": round(s, 1), "min": lo, "max": hi,
                       "freq": freq, "status": status})
    p_vol = 35 * sum(notas_vol) / len(notas_vol)
    p_freq = 20 * sum(notas_freq) / len(notas_freq)
    if baixos:
        grave = any(v["status"] == "baixo" and v["series"] < v["min"] * 0.5 for v in volume)
        msg("critico" if grave else "alerta",
            "Volume semanal abaixo do recomendado: " + "; ".join(baixos) + ".")
    if altos:
        msg("alerta", "Volume acima do que a maioria consegue recuperar: " + "; ".join(altos) +
            ". Séries demais viram \"volume lixo\" — prefira menos séries com mais intensidade.")
    if not baixos and not altos:
        msg("ok", "Volume semanal dentro da faixa ideal em todos os músculos principais.")
    if freq_baixa:
        msg("alerta", "Treinados só 1x por semana: " + ", ".join(freq_baixa) +
            ". Dividir o volume em 2 sessões semanais costuma render mais.")
    elif not baixos:
        msg("ok", "Frequência de pelo menos 2x por semana nos músculos principais.")

    # 2) Duração ---------------------------------------------------------------
    notas_dur = []
    for d in dias:
        t = tempo_dia(d["exercicios"])
        if 40 <= t <= 90:
            notas_dur.append(1)
        elif 30 <= t < 40 or 90 < t <= 105:
            notas_dur.append(0.7)
        else:
            notas_dur.append(0.35)
        if t > 105:
            msg("alerta", f"\"{d['nome']}\" leva cerca de {t} min. Acima de ~90 min a qualidade "
                "das últimas séries cai; corte exercícios redundantes ou divida em mais dias.")
        elif t < 30:
            msg("dica", f"\"{d['nome']}\" tem só ~{t} min. Há espaço para mais trabalho.")
    p_dur = 15 * sum(notas_dur) / len(notas_dur)

    # 3) Seleção e ordem -------------------------------------------------------
    todos = [(BY_ID[i["id"]], i) for d in dias for i in d["exercicios"]]
    media_nivel = sum(e["nivel"] for e, _ in todos) / len(todos)
    ordem_ruim = 0
    for d in dias:
        exs = [BY_ID[i["id"]] for i in d["exercicios"]]
        for k, e in enumerate(exs):
            if not e["composto"] and e["musculo"] in ("peito", "costas", "quadriceps", "posterior") \
                    and any(o["composto"] and o["musculo"] == e["musculo"] for o in exs[k + 1:]):
                ordem_ruim += 1
                msg("dica", f"Em \"{d['nome']}\", {e['nome']} vem antes de um composto de "
                    f"{MUSCLES[e['musculo']].lower()}. Fazer o composto primeiro permite mais carga.")
                break
    chave = [m for m in ("peito", "costas", "biceps", "triceps", "quadriceps", "posterior")
             if any(e["musculo"] == m for e, _ in todos)]
    com_along = [m for m in chave if any(e["musculo"] == m and e["alongado"] for e, _ in todos)]
    sem_along = [MUSCLES[m] for m in chave if m not in com_along]
    p_sel = (8 * (media_nivel - 1) / 2 + 4 * (1 - min(1, ordem_ruim / len(dias))) +
             3 * (len(com_along) / len(chave) if chave else 0))
    fracos = sorted({e["nome"] for e, _ in todos if e["nivel"] == 1})
    if fracos:
        msg("dica", "Exercícios com menor potencial de hipertrofia: " + ", ".join(fracos[:5]) +
            ". Use \"Trocar\" para ver opções melhores com o seu equipamento.")
    if sem_along:
        msg("dica", "Sem exercício com tensão na posição alongada para: " + ", ".join(sem_along) +
            ". Esse tipo de exercício tende a gerar mais hipertrofia.")
    if media_nivel >= 2.5 and not ordem_ruim:
        msg("ok", "Ótima seleção de exercícios, com compostos antes dos isolados.")
    for d in dias:
        for it in d["exercicios"]:
            e = BY_ID[it["id"]]
            media, seg = _reps_info(it["reps"])
            if not seg and (media < 4 or media > 30):
                msg("alerta", f"{e['nome']}: {it['reps']} repetições está fora da faixa útil "
                    "para hipertrofia (5 a 30, idealmente 6 a 15).")
            if e["padrao"] in HEAVY and it["descanso"] < 90:
                msg("alerta", f"{e['nome']}: descanso de {it['descanso']}s é curto para um "
                    "composto pesado. Use 2 a 3 minutos para manter a carga nas séries.")
            if it["series"] > 5:
                msg("dica", f"{e['nome']}: {it['series']} séries no mesmo exercício rende pouco "
                    "a mais. Melhor dividir em dois exercícios diferentes.")

    # 4) Equilíbrio ------------------------------------------------------------
    push = sum(i["series"] for e, i in todos if e["padrao"] in PUSH)
    pull = sum(i["series"] for e, i in todos if e["padrao"] in PULL)
    p_bal = 0
    if push == 0 or pull >= push * 0.8:
        p_bal += 5
    else:
        msg("alerta", f"Desequilíbrio empurrar/puxar: {push} séries de empurrar contra {pull} "
            "de puxar. Iguale para proteger os ombros e melhorar a postura.")
    quad, post = semana.get("quadriceps", 0), semana.get("posterior", 0)
    if quad == 0 or post >= quad * 0.5:
        p_bal += 5
    else:
        msg("alerta", f"Posterior de coxa ({post:g} séries) muito abaixo do quadríceps "
            f"({quad:g}). Adicione flexora ou stiff.")
    limite = 12 if nivel == "avancado" else 10
    excesso = [f"{MUSCLES[m]} em \"{d['nome']}\" ({v:g})" for d, vd in zip(dias, por_dia)
               for m, v in vd.items() if v > limite and faixa(m, nivel)[0] > 0]
    if not excesso:
        p_bal += 5
    else:
        msg("alerta", "Séries demais para o mesmo músculo numa única sessão: " +
            "; ".join(excesso) + f". Acima de ~{limite} por sessão o retorno cai bastante.")
    if not semana.get("quadriceps") and not semana.get("posterior"):
        msg("critico", "O treino não tem pernas. Treinar o corpo todo é essencial para um físico completo.")

    nota = round(p_vol + p_freq + p_dur + p_sel + p_bal)
    ordem = {"critico": 0, "alerta": 1, "dica": 2, "ok": 3}
    msgs.sort(key=lambda m: ordem[m["tipo"]])
    return {
        "vazio": False,
        "nota": nota,
        "conceito": _conceito(nota),
        "criterios": [
            {"nome": "Volume semanal", "pontos": round(p_vol, 1), "max": 35},
            {"nome": "Frequência", "pontos": round(p_freq, 1), "max": 20},
            {"nome": "Duração das sessões", "pontos": round(p_dur, 1), "max": 15},
            {"nome": "Seleção e ordem", "pontos": round(p_sel, 1), "max": 15},
            {"nome": "Equilíbrio", "pontos": round(p_bal, 1), "max": 15},
        ],
        "volume": volume,
        "dias": info_dias,
        "mensagens": msgs,
    }
