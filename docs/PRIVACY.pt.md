# Política de Privacidade

Data de vigência: 25-09-2025

Esta Política de Privacidade descreve como a faucet auto-hospedável Pay2Slay (o "Software") processa dados de usuário. O objetivo é a máxima privacidade e mínima retenção de dados. Espera-se que os implantadores ("Operadores") sigam ou melhorem estes princípios.

## Princípios orientadores
- Minimização de dados: Armazene apenas o estritamente necessário para cálculo correto de recompensas, prevenção de abuso e auditoria.
- Apenas local por padrão: Nenhuma telemetria, anúncio ou beacon de rastreamento é emitido. Todas as métricas/traces ficam na infraestrutura do operador, a menos que configurado explicitamente.
- Efemeridade: Dados voláteis ou deriváveis (ex. estado de sessão, trocas OAuth transitórias) não são persistidos além da necessidade funcional.
- Transparência ao usuário: Categorias de dados e propósitos estão documentados abaixo; sem processamento oculto.
- Amigável à exclusão: Recursos opcionais (exportação de tracing, analytics estendidas) ficam desabilitados a menos que o operador os habilite.

## Categorias de dados
| Categoria | Exemplos | Propósito | Retenção | Notas |
|-----------|----------|-----------|----------|-------|
| Identidade (Discord) | discord_user_id, username, flag de membro do guild | Elegibilidade + atribuição de recompensas | Até solicitação de exclusão ou purga do operador | Nenhum scope privilegiado solicitado além de identidade+verificação de guild. |
| Identidade (Fortnite) | epic_account_id | Vincular atividade ao usuário para deltas de abates | Até exclusão ou desvinculação da conta | Originado via mapeamento Yunite; não compartilhado externamente. |
| Carteira | Endereço Banano (primário) | Entregar pagamentos | Até desvinculação ou exclusão | Múltiplos endereços opcionais; apenas o primário para pagamentos. |
| Atividade de recompensas | RewardAccrual (abates, valor, epoch_minute) | Calcular pagamentos / auditar abuso | Até liquidação + (janela de auditoria definida pelo operador) | Pode ser podada após finalização do pagamento. |
| Registros de pagamento | valor, tx_hash, status, metadados de tentativas | Responsabilidade financeira / retry / resolução de disputas | Indefinido ou conforme operador | tx_hash pode ser público on-chain de qualquer forma. |
| Eventos de verificação | VerificationRecord (fonte, status, timestamps) | Rastrear histórico de verificação / resolução de disputas | Janela rolante ou indefinido conforme operador | Pode ser agressivamente podado (manter último bem-sucedido). |
| Flags de abuso | flag_type, severity, detail | Proteger uso justo / integridade | Até limpeza ou exclusão do usuário | Apenas resumos heurísticos; sem armazenamento de IP. |
| Registros de doação | DonationLedger (amount_ban, blocks_received, source) | Rastrear doações da comunidade, progresso de marcos | Indefinido ou conforme operador | Nenhuma identidade do doador armazenada; apenas valores. |
| Código de região (aproximado) | ex. "eu", "na" | Análise de abuso, estatísticas de distribuição de pagamentos | Opcional; pode ser desabilitado | Derivado de header ou mapeamento IP aproximado; nunca geo precisa. |
| Logs (estruturados) | nomes de eventos, trace/span IDs (se habilitado) | Debug e auditoria | Retenção curta recomendada (ex. 7–30 dias) | Excluir segredos via helper de mascaramento. |
| Sessões | Token de sessão HMAC (cookie) | Autenticar requisições subsequentes | Apenas em memória / TTL do cookie | Tokens opacos e revogáveis limpando cookie. |

## O que deliberadamente NÃO coletamos
- Sem email, nome real, data de nascimento, identidade governamental, telefone.
- Sem geolocalização precisa, retenção de IP ou IDs de analytics de terceiros.
- Sem perfilamento comportamental ou segmentação de marketing.
- Sem dados biométricos ou de categoria sensível.

## Recursos opcionais / controlados pelo operador
| Recurso | Padrão | Impacto na privacidade | Mitigação |
|---------|--------|----------------------|-----------|
| Exportação OpenTelemetry | Desabilitado | Poderia exportar spans (inclui nomes de rota, timings) | Manter endpoint de exportação interno ou deixar desabilitado |
| Middleware regional estendido | Habilitado (apenas aproximado) | Código de região mínimo aproximado | Desabilitar via config se indesejado |
| Endpoint de métricas (/metrics) | Habilitado | Expõe contadores agregados | Proteger via política de rede / gateway de auth |
| IDs de trace em logs | Habilitado (local) | Correlaciona eventos de requisição | Evitar exportar logs para terceiros sem revisão |

## Controles do titular dos dados
Operadores devem fornecer (através de seu canal de deploy):
- Direito de acesso: Endpoint ou processo para o usuário visualizar identidade e histórico de pagamentos armazenados (parcialmente coberto por endpoints existentes `/me/status`, `/me/payouts`).
- Direito de exclusão: Script do operador ou ação admin para excluir (ou anonimizar) usuário, em cascata para vínculos de carteira, acumulações (liquidadas), flags, sessões.
- Direito de retificação: Re-disparar verificação para atualizar mapeamento Epic (/me/reverify ou re-verificação admin).

## Medidas de segurança
- Tokens de sessão assinados com segredo HMAC (não adivinhável; sem PII dentro).
- Segredos mascarados em logs estruturados (`safe_dict`).
- Rate limiting e heurísticas de abuso reduzem scraping/enumeração automatizada.
- Proteção opcional de saldo do operador previne pagamentos vazios não intencionados.

## Guia de retenção (recomendado)
| Dados | Retenção máx. sugerida | Método de eliminação |
|-------|------------------------|----------------------|
| Linhas de acumulação brutas | 30–90 dias pós-liquidação | Excluir ou agregar apenas estatísticas |
| Registros de verificação (anteriores ao último bem-sucedido) | 30 dias | Purgar |
| Flags de abuso (resolvidos) | 90 dias | Purgar |
| Logs | 7–30 dias | Rotacionar + destruir |
| TSDB de métricas | 30–90 dias | Política de retenção |

## Internacional e transferências
O Software não transmite dados para fora da infraestrutura do operador a menos que configurado explicitamente (ex. endpoint de tracing externo). Quaisquer considerações de transferência entre regiões cabem às escolhas de hosting do operador. Nenhuma lógica de transferência automática ao exterior existe no código.

## Dados de menores
O Software não é projetado para coletar indicadores de idade; operadores devem restringir promoção para públicos apropriados conforme sua jurisdição.

## Alterações nesta política
Versionada no controle de código fonte. Alterações materiais devem incrementar a Data de vigência e resumir diferenças nas mensagens de commit.

## Contato / Governança
Como projeto auto-hospedado, responsabilidades de governança e conformidade são de cada operador. Contribuições da comunidade para fortalecer a privacidade são bem-vindas via pull request.

## Checklist rápido do operador
- [ ] Desabilitar exportação OTLP a menos que necessário
- [ ] Proteger /metrics atrás de auth ou política de rede
- [ ] Definir retenção de logs ≤30d
- [ ] Fornecer procedimento documentado de exclusão de usuário
- [ ] Podar periodicamente acumulações liquidadas e registros de verificação obsoletos
- [ ] Revisar configs para exposição acidental de segredos

---
Esta política visa a máxima privacidade com mínima fricção. Se você pode remover ou anonimizar mais mantendo as recompensas precisas — faça-o e contribua melhorias.
