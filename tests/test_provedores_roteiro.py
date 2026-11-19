import json
import sys
import types
import unittest
from unittest.mock import patch

import criar_video as cv


class ProvedoresRoteiroTests(unittest.TestCase):
    def test_resolve_provedor_independente_por_etapa(self):
        cfg = {
            "provedor_planejamento_narrativa": "myhub",
            "provedor_geracao_roteiro": "gemini",
            "provedor_refino_roteiro": "myhub",
        }
        self.assertEqual(cv._provedor_texto_etapa(cfg, "planejamento"), "myhub")
        self.assertEqual(cv._provedor_texto_etapa(cfg, "roteiro"), "gemini")
        self.assertEqual(cv._provedor_texto_etapa(cfg, "refino"), "myhub")

    def test_padrao_novo_e_myhub_em_todas_as_etapas(self):
        self.assertEqual(cv.PADROES["provedor_planejamento_narrativa"], "myhub")
        self.assertEqual(cv.PADROES["provedor_geracao_roteiro"], "myhub")
        self.assertEqual(cv.PADROES["provedor_refino_roteiro"], "myhub")
        self.assertEqual(cv.PADROES["m1_diretor_padrao"], "myhub")

    def test_rota_planejamento_roteiro_e_refino_para_myhub(self):
        calls = []
        respostas = {
            "planejamento": json.dumps({
                "pergunta_central": "Pergunta central", "conflito": "Mistério",
                "revelacoes": ["Revelação 1"], "pico": "Pico",
                "recompensa": "Recompensa", "final": "Final", "perguntas_ponte": [],
            }),
            "roteiro": json.dumps({
                "titulo": "Teste MyHub", "descricao": "Teste", "tags": [],
                "gancho_escolhido": {"texto": "Uma pergunta interessante?"},
                "cenas": [{"narracao": "Uma pergunta interessante?"},
                          {"narracao": "Esta é a resposta concreta."},
                          {"narracao": "E aqui está o encerramento."}],
            }),
            "checagem": json.dumps({"resultado": []}),
            "otimizacao": json.dumps({"narracoes": []}),
            "refino": json.dumps({"narracoes": []}),
        }

        def factory(cfg, root, log, *, purpose=None, expected_outputs=None, **kwargs):
            calls.append((purpose, list(expected_outputs or [])))
            return lambda prompt, json_mode=True: respostas[purpose]

        fake = types.SimpleNamespace(criar_llm_myhub=factory)
        canal = {"nome": "Canal teste", "segundos_por_imagem": 8, "proporcao_video": 0.5,
                 "regras_globais": [], "duracao_alvo_segundos": 30}
        cfg = {
            "provedor_planejamento_narrativa": "myhub",
            "provedor_geracao_roteiro": "myhub",
            "provedor_refino_roteiro": "myhub",
            "otimizar_roteiro": True,
            "refinar_roteiro": True,
            "gemini_api_key": "",
        }
        plano = {"retencao": {"tensao": "alta"}, "cta": "Qual ponto chamou sua atenção?"}
        with patch.dict(sys.modules, {"myhub_llm": fake}), \
             patch.object(cv, "resolver_nucleo", return_value={"modo": "legado", "perfil_id": ""}), \
             patch.object(cv, "closing_instruction", return_value="Pergunta final específica"), \
             patch.object(cv, "planejar_narrativa", side_effect=lambda tema, res, n, dur, chamar: json.loads(chamar("planejamento"))), \
             patch.object(cv, "montar_prompt_roteiro", return_value="prompt do roteiro"), \
             patch.object(cv, "construir_plano", return_value=plano), \
             patch.object(cv, "avaliar_roteiro", return_value={"score": 90, "cenas_sem_gancho": []}), \
             patch.object(cv, "perguntas_sem_resposta", side_effect=lambda cenas, chamar: (chamar("checagem"), [])[1]), \
             patch.object(cv, "otimizar_roteiro_completo", side_effect=lambda r, p, av, ruins, chamar, pn: (chamar("otimizacao") and r, {"aplicado": False})), \
             patch.object(cv, "refinar_roteiro", side_effect=lambda r, p, chamar: (chamar("refino") and r, {"aplicado": False})), \
             patch.object(cv, "nota_7_criterios", return_value={"nota": 9}):
            result = cv.gerar_roteiro(canal, "Tema de teste", 30, [], cfg)

        self.assertEqual({x[0] for x in calls}, {"planejamento", "roteiro", "checagem", "otimizacao", "refino"})
        self.assertTrue(all(x[1] == ["json"] for x in calls))
        self.assertEqual(result["provedores_ia"], {"planejamento": "myhub", "roteiro": "myhub", "refino": "myhub"})

    def test_salvar_provedores_preserva_chaves_e_faz_backup(self):
        import tempfile
        import app
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            config = root / "config.json"
            config.write_text(json.dumps({"gemini_api_key": "MANTER", "pixabay_api_key": "MANTER_TAMBEM"}), encoding="utf-8")
            with patch.object(app, "RAIZ", root):
                result = app.salvar_provedores_ia({
                    "provedor_planejamento_narrativa": "myhub",
                    "provedor_geracao_roteiro": "myhub",
                    "provedor_refino_roteiro": "gemini",
                    "m1_diretor_padrao": "myhub",
                })
            saved = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(saved["gemini_api_key"], "MANTER")
            self.assertEqual(saved["pixabay_api_key"], "MANTER_TAMBEM")
            self.assertEqual(saved["provedor_refino_roteiro"], "gemini")
            self.assertTrue((root / "config.json.backup_provedores").exists())
            self.assertEqual(result["m1_diretor_padrao"], "myhub")

    def test_configurar_script_preserva_config_existente(self):
        import tempfile
        import configurar_provedores_myhub as setup
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            config = root / "config.json"
            config.write_text(json.dumps({"api_key": "SEGREDO_NAO_APAGAR", "imagem_ia": True}), encoding="utf-8")
            with patch.object(setup, "ROOT", root), patch.object(setup, "CONFIG", config):
                self.assertEqual(setup.main(), 0)
            saved = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(saved["api_key"], "SEGREDO_NAO_APAGAR")
            self.assertTrue(saved["imagem_ia"])
            self.assertEqual(saved["provedor_geracao_roteiro"], "myhub")
            self.assertTrue(list(root.glob("config.json.backup_myhub_*.")) == [] or list(root.glob("config.json.backup_myhub_*")))


if __name__ == "__main__":
    unittest.main()
