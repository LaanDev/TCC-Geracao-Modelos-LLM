import { useState } from 'react'
import './App.css'

// URL base da API (em dev o Vite faz proxy de /api para 127.0.0.1:8000)
const API_BASE = '/api'

export default function App() {
  const [descricao, setDescricao] = useState(
    'Um sistema é composto por um bloco de massa M e uma mola K. Encontre a função de transferência G(s) = X(s)/F(s).'
  )
  const [funcaoUsuario, setFuncaoUsuario] = useState('G(s) = 1 / (Ms² + K)')
  const [loading, setLoading] = useState(false)
  const [resultado, setResultado] = useState(null)
  const [erro, setErro] = useState(null)

  async function chamarAPI(endpoint, body) {
    setLoading(true)
    setErro(null)
    setResultado(null)
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      if (!res.ok) {
        setErro(data.erro || `Erro ${res.status}`)
        return
      }
      setResultado(data)
    } catch (err) {
      setErro(err.message || 'Falha ao conectar na API. Verifique se a API está rodando (python main.py).')
    } finally {
      setLoading(false)
    }
  }

  function gerarApenasFT() {
    chamarAPI('/gerar-apenas-ft', { descricao })
  }

  function gerarAnaliseCompleta() {
    chamarAPI('/gerar-analise-completa', { descricao })
  }

  function validarResposta() {
    chamarAPI('/validar-minha-resposta', {
      descricao,
      funcao_transferencia_usuario: funcaoUsuario,
    })
  }

  return (
    <div className="app">
      <header className="header">
        <h1>TCC – Modelagem de Sistemas de Controle</h1>
        <p className="subtitle">Descreva o sistema e use a IA para obter a função de transferência</p>
      </header>

      <main className="main">
        <section className="card form-card">
          <h2>Descrição do sistema</h2>
          <textarea
            className="textarea"
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            placeholder="Ex: Um circuito RC série com saída no capacitor..."
            rows={4}
          />

          <div className="validar-campo">
            <label htmlFor="ft-usuario">Sua função de transferência (só para “Validar”)</label>
            <input
              id="ft-usuario"
              type="text"
              className="input"
              value={funcaoUsuario}
              onChange={(e) => setFuncaoUsuario(e.target.value)}
              placeholder="Ex: G(s) = 1 / (RCs + 1)"
            />
          </div>

          <div className="botoes">
            <button
              className="btn btn-primary"
              onClick={gerarApenasFT}
              disabled={loading || !descricao.trim()}
            >
              Gerar apenas FT
            </button>
            <button
              className="btn btn-secondary"
              onClick={gerarAnaliseCompleta}
              disabled={loading || !descricao.trim()}
            >
              Análise completa
            </button>
            <button
              className="btn btn-outline"
              onClick={validarResposta}
              disabled={loading || !descricao.trim() || !funcaoUsuario.trim()}
            >
              Validar minha resposta
            </button>
          </div>
        </section>

        {(loading || resultado || erro) && (
          <section className="card result-card">
            {loading && (
              <div className="loading">
                <span className="spinner" /> Aguardando resposta da API...
              </div>
            )}
            {erro && (
              <div className="erro">
                <strong>Erro:</strong> {erro}
              </div>
            )}
            {resultado && !loading && (
              <div className="resultado">
                <h3>Resultado</h3>
                <pre className="json">{JSON.stringify(resultado, null, 2)}</pre>
              </div>
            )}
          </section>
        )}
      </main>

      <footer className="footer">
        <p>API em <code>http://127.0.0.1:8000</code> · Docs: <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noopener noreferrer">/docs</a></p>
      </footer>
    </div>
  )
}
