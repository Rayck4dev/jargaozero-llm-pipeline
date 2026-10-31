import { useState } from 'react'

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:1235/v1'
).replace(/\/+$/, '')
const CONFIGURED_MODEL = import.meta.env.VITE_LLM_MODEL?.trim()

const NO_MODEL_MESSAGE =
  'Nenhum modelo está carregado no LM Studio. Abra a página Developer, selecione o modelo e clique em Load. A opção “Modelo raiz” nas configurações não carrega o modelo por si só.'

async function getModelForRequest() {
  if (CONFIGURED_MODEL) return CONFIGURED_MODEL

  const response = await fetch(`${API_BASE_URL}/models`)
  const data = await response.json()

  if (!response.ok) {
    throw new Error(
      data.error?.message ||
        `Não foi possível consultar os modelos locais (erro ${response.status}).`,
    )
  }

  const model = data.data?.[0]?.id
  if (!model) throw new Error(NO_MODEL_MESSAGE)

  return model
}

const examples = [
  {
    label: 'Cache-Aside',
    text: 'O padrão Cache-Aside verifica primeiro o cache e, se os dados não estiverem lá, busca no banco de dados e guarda uma cópia para a próxima consulta.',
  },
  {
    label: 'Microsserviços',
    text: 'Microsserviços são pequenos serviços independentes que trabalham juntos para formar uma aplicação.',
  },
  {
    label: 'Latência de rede',
    text: 'A latência de rede é o tempo que os dados levam para ir de um ponto a outro pela internet.',
  },
]

const levels = [
  {
    value: 'Leigo',
    title: 'Sem complicação',
    description: 'Para qualquer pessoa',
  },
  {
    value: 'Intermediário',
    title: 'Com contexto',
    description: 'Para quem está aprendendo',
  },
  {
    value: 'Técnico',
    title: 'Mais detalhes',
    description: 'Para quem já conhece a área',
  },
]

function Icon({ name, size = 20 }) {
  const sharedProps = {
    'aria-hidden': true,
    fill: 'none',
    height: size,
    stroke: 'currentColor',
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    strokeWidth: 1.8,
    viewBox: '0 0 24 24',
    width: size,
  }

  if (name === 'sparkle') {
    return (
      <svg {...sharedProps}>
        <path d="m12 3 1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2L12 3Z" />
        <path d="m19 14 .9 2.1L22 17l-2.1.9L19 20l-.9-2.1L16 17l2.1-.9L19 14Z" />
      </svg>
    )
  }

  if (name === 'arrow') {
    return (
      <svg {...sharedProps}>
        <path d="M5 12h14" />
        <path d="m13 6 6 6-6 6" />
      </svg>
    )
  }

  if (name === 'copy') {
    return (
      <svg {...sharedProps}>
        <rect height="13" rx="2" width="13" x="8" y="8" />
        <path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3" />
      </svg>
    )
  }

  if (name === 'check') {
    return (
      <svg {...sharedProps}>
        <path d="m5 12 4 4L19 6" />
      </svg>
    )
  }

  return (
    <svg {...sharedProps}>
      <path d="M12 3 2.8 19a1.3 1.3 0 0 0 1.1 2h16.2a1.3 1.3 0 0 0 1.1-2L12 3Z" />
      <path d="M12 9v4" />
      <path d="M12 17h.01" />
    </svg>
  )
}

function App() {
  const [termo, setTermo] = useState('')
  const [nivel, setNivel] = useState('Leigo')
  const [resposta, setResposta] = useState(null)
  const [erro, setErro] = useState('')
  const [loading, setLoading] = useState(false)
  const [copiado, setCopiado] = useState(false)
  const [erroCopia, setErroCopia] = useState('')

  const handleTraduzir = async (event) => {
    event.preventDefault()
    if (!termo.trim() || loading) return

    setLoading(true)
    setErro('')
    setResposta(null)
    setCopiado(false)
    setErroCopia('')

    const prompt = `Entrada: Nível: ${nivel}. Texto: ${termo.trim()}\nSaída:`

    try {
      const model = await getModelForRequest()
      const response = await fetch(`${API_BASE_URL}/chat/completions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model,
          messages: [
            {
              role: 'system',
              content:
                'Atue exclusivamente como o tradutor do projeto JargãoZero. Explique termos e textos técnicos em português claro, adequando a explicação ao nível solicitado. Seja direto, sem incluir tags, metadados ou explicações adicionais.',
            },
            {
              role: 'user',
              content:
                'Entrada: Nível: Leigo. Texto: A latência de rede refere-se ao atraso temporal na propagação de pacotes de dados através de um meio de comunicação.\nSaída: É o tempo de espera desde o momento em que você clica em algo na internet até a página carregar na tela.',
            },
            { role: 'user', content: prompt },
          ],
          temperature: 0.3,
          max_tokens: 200,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.error?.message ||
          `A API local respondeu com o erro ${response.status}.`,
        )
      }

      const explicacao = data.choices?.[0]?.message?.content?.trim()
      if (!explicacao) {
        throw new Error('A API respondeu, mas não trouxe uma explicação.')
      }

      setResposta({ termo: termo.trim(), nivel, explicacao })
    } catch (error) {
      console.error('Erro ao conectar com a API local:', error)
      setErro(
        error instanceof TypeError
          ? 'Não foi possível conectar. Confira se o LM Studio está aberto, com um modelo carregado e o servidor local ativo na porta 1235.'
          : /no models loaded/i.test(error.message)
            ? NO_MODEL_MESSAGE
            : error.message,
      )
    } finally {
      setLoading(false)
    }
  }

  const handleCopiar = async () => {
    if (!resposta) return
    setErroCopia('')

    try {
      await navigator.clipboard.writeText(resposta.explicacao)
      setCopiado(true)
      window.setTimeout(() => setCopiado(false), 1800)
    } catch (error) {
      console.error('Não foi possível copiar a explicação:', error)
      setErroCopia('Selecione e copie o texto manualmente.')
    }
  }

  return (
    <div className="app-shell">
      <main className="main-content" id="inicio">
        <div className="content-wrap" id="tradutor">
          <a aria-label="JargãoZero, início" className="brand" href="#inicio">
            <span className="brand-mark">
              <Icon name="sparkle" size={23} />
            </span>
            <span className="brand-name">
              Jargão<span>Zero</span>
            </span>
          </a>

          <section aria-labelledby="page-title" className="intro">
            <div className="eyebrow">
              <span className="eyebrow-line" />
              MENOS JARGÃO. MAIS CLAREZA.
            </div>
            <h3 id="page-title">
              Tecnologia que <span>todo mundo entende.</span>
            </h3>
            <p className="intro-copy">
              Cole um texto técnico e receba uma explicação feita para o seu jeito de aprender.
            </p>
          </section>

          <section aria-label="Tradução de texto técnico" className="workspace">
            <form className="composer-card" onSubmit={handleTraduzir}>
              <div className="card-heading">
                <div>
                  <span className="step-label">PASSO 01</span>
                  <h2>O que vamos simplificar?</h2>
                </div>
                <span className="heading-icon">
                  <Icon name="sparkle" size={20} />
                </span>
              </div>

              <label className="field-label" htmlFor="termo">
                SEU TEXTO TÉCNICO
              </label>
              <div className="textarea-wrap">
                <textarea
                  id="termo"
                  maxLength={2000}
                  onChange={(event) => setTermo(event.target.value)}
                  placeholder="Cole aqui aquela explicação cheia de termos difíceis..."
                  value={termo}
                />
                <span className="character-count tabular-nums">
                  {termo.length}/2000
                </span>
              </div>

              <div className="examples">
                <span className="examples-label">OU EXPERIMENTE</span>
                <div className="example-chips">
                  {examples.map((example) => (
                    <button
                      className="example-chip"
                      key={example.label}
                      onClick={() => {
                        setTermo(example.text)
                        setErro('')
                      }}
                      type="button"
                    >
                      {example.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="level-section">
                <span className="field-label">QUANTO DETALHE VOCÊ QUER?</span>
                <div aria-label="Nível de explicação" className="level-options">
                  {levels.map((option, index) => (
                    <button
                      aria-pressed={nivel === option.value}
                      className={`level-option${nivel === option.value ? ' selected' : ''}`}
                      key={option.value}
                      onClick={() => setNivel(option.value)}
                      type="button"
                    >
                      <span className="level-option-title">
                        <span className="level-number">0{index + 1}</span>
                        {option.title}
                      </span>
                      <span className="level-description">
                        {option.description}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              <button
                className="submit-button"
                disabled={!termo.trim() || loading}
                type="submit"
              >
                {loading ? (
                  <>
                    <span aria-hidden="true" className="loading-spinner" />
                    Preparando sua explicação...
                  </>
                ) : (
                  <>
                    Simplificar texto
                    <Icon name="arrow" size={18} />
                  </>
                )}
              </button>
            </form>

            <section
              aria-busy={loading}
              aria-live="polite"
              className={`result-card${resposta ? ' has-result' : ''}`}
            >
              <div className="result-heading">
                <div>
                  <span className="step-label">PASSO 02</span>
                  <h2>Em português claro</h2>
                </div>
                {resposta && (
                  <button
                    aria-label={copiado ? 'Texto copiado' : 'Copiar explicação'}
                    className={`copy-button${copiado ? ' copied' : ''}`}
                    onClick={handleCopiar}
                    type="button"
                  >
                    <Icon name={copiado ? 'check' : 'copy'} size={16} />
                    {copiado ? 'Copiado!' : 'Copiar'}
                  </button>
                )}
              </div>

              {loading ? (
                <div className="result-empty loading-state">
                  <span className="loading-orb">
                    <span className="loading-spinner" />
                  </span>
                  <h3>Traduzindo para o simples...</h3>
                  <p>A IA está preparando uma explicação.</p>
                </div>
              ) : resposta ? (
                <div className="result-content">
                  <span className="result-tag">
                    <Icon name="sparkle" size={14} />
                    EXPLICAÇÃO SIMPLIFICADA
                  </span>
                  <p className="result-term">{resposta.termo}</p>
                  <p className="result-explanation">{resposta.explicacao}</p>
                  <div className="result-meta">
                    <span className="meta-level">
                      Nível: <strong>{resposta.nivel}</strong>
                    </span>
                    <span className="result-model">
                      <span className="status-dot" />
                      Gerado localmente
                    </span>
                  </div>
                </div>
              ) : (
                <div className="result-empty">
                  <div aria-hidden="true" className="empty-art">
                    <span className="art-glow" />
                    <span className="art-orbit orbit-one" />
                    <span className="art-orbit orbit-two" />
                    <span className="art-core">
                      <Icon name="sparkle" size={29} />
                    </span>
                    <span className="art-star star-one">✳</span>
                    <span className="art-star star-two">✦</span>
                  </div>
                  <h3>A clareza começa aqui.</h3>
                  <p>
                    Sua explicação simplificada vai aparecer neste espaço.
                  </p>
                  <div className="empty-prompt">
                    <span className="prompt-dot" />
                    Escolha um exemplo ou escreva seu próprio texto
                  </div>
                </div>
              )}

              {erro && (
                <div className="error-message" role="alert">
                  <span className="error-icon">
                    <Icon name="alert" size={17} />
                  </span>
                  <div>
                    <strong>Não foi possível concluir.</strong>
                    <p>{erro}</p>
                  </div>
                </div>
              )}

              {erroCopia && (
                <div className="error-message" role="alert">
                  <span className="error-icon">
                    <Icon name="alert" size={17} />
                  </span>
                  <div>
                    <strong>Não foi possível copiar.</strong>
                    <p>{erroCopia}</p>
                  </div>
                </div>
              )}

              {!resposta && !loading && !erro && (
                <div className="result-footer">
                  <span className="footer-sparkle">
                    <Icon name="sparkle" size={15} />
                  </span>
                  Feito para deixar a tecnologia mais acessível.
                </div>
              )}
            </section>
          </section>

        </div>
      </main>
    </div>
  )
}

export default App
