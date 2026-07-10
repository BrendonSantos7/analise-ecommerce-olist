USE olist_dw;
GO

-- PERGUNTA: como evoluiu o faturamento mes a mes?
-- Isso responde a pergunta de sazonalidade do README da Olist

SELECT
    t.ano,
    t.mes,
    t.nome_mes,
    COUNT(DISTINCT f.order_id)        AS total_pedidos,
    COUNT(*)                          AS total_itens,
    ROUND(SUM(f.valor_produto), 2)    AS receita_produtos,
    ROUND(SUM(f.valor_frete),   2)    AS receita_frete,
    ROUND(SUM(f.valor_total_item), 2) AS faturamento_total,
    ROUND(AVG(f.valor_produto), 2)    AS ticket_medio
FROM fato_pedidos f
JOIN dim_tempo t ON f.sk_tempo = t.sk_tempo
WHERE f.status_pedido NOT IN ('canceled', 'unavailable')
GROUP BY t.ano, t.mes, t.nome_mes
ORDER BY t.ano, t.mes;

-- PERGUNTA: quais categorias de produto geram mais receita?
-- Responde: "nosso catalogo tem foco em categorias especificas?"

SELECT TOP 10
    p.categoria_ingles                    AS categoria,
    COUNT(DISTINCT f.order_id)            AS total_pedidos,
    COUNT(*)                              AS total_itens_vendidos,
    ROUND(SUM(f.valor_produto), 2)        AS faturamento,
    ROUND(AVG(f.valor_produto), 2)        AS ticket_medio,
    ROUND(AVG(f.nota_avaliacao * 1.0), 2) AS nota_media
FROM fato_pedidos f
JOIN dim_produtos p ON f.sk_produto = p.sk_produto
WHERE f.status_pedido NOT IN ('canceled', 'unavailable')
GROUP BY p.categoria_ingles
ORDER BY faturamento DESC;

-- PERGUNTA: existe diferenca no frete praticado por regiao?
-- Responde diretamente uma das perguntas do README da Olist

SELECT
    c.estado,
    COUNT(DISTINCT f.order_id)             AS total_pedidos,
    ROUND(AVG(f.valor_frete), 2)           AS frete_medio,
    ROUND(AVG(f.valor_produto), 2)         AS ticket_medio,
    ROUND(AVG(f.dias_para_entregar), 1)    AS dias_entrega_medio,
    ROUND(AVG(f.nota_avaliacao * 1.0), 2)  AS nota_media
FROM fato_pedidos f
JOIN dim_clientes c ON f.sk_cliente = c.sk_cliente
WHERE f.status_pedido = 'delivered'
  AND f.dias_para_entregar IS NOT NULL
GROUP BY c.estado
ORDER BY total_pedidos DESC;

-- PERGUNTA: quem sao os top vendedores? merecem beneficios diferenciados?
-- Responde diretamente uma das perguntas do README

-- CTE = voce define uma "tabela temporaria com nome" antes do SELECT principal
-- Equivalente a criar uma #temp table, mas mais elegante e legivel
-- Sintaxe: WITH nome_da_cte AS ( query aqui ) SELECT ... FROM nome_da_cte

WITH vendedor_performance AS (
    SELECT
        f.sk_vendedor,
        COUNT(DISTINCT f.order_id)            AS total_pedidos,
        COUNT(*)                              AS total_itens,
        ROUND(SUM(f.valor_produto), 2)        AS faturamento,
        ROUND(AVG(f.valor_produto), 2)        AS ticket_medio,
        ROUND(AVG(f.nota_avaliacao * 1.0), 2) AS nota_media,
        ROUND(AVG(f.dias_para_entregar*1.0), 1) AS dias_entrega_medio
    FROM fato_pedidos f
    WHERE f.status_pedido NOT IN ('canceled', 'unavailable')
    GROUP BY f.sk_vendedor
)
SELECT TOP 10
    v.seller_id,
    v.cidade,
    v.estado,
    vp.total_pedidos,
    vp.total_itens,
    vp.faturamento,
    vp.ticket_medio,
    vp.nota_media,
    vp.dias_entrega_medio
FROM vendedor_performance vp
JOIN dim_vendedores v ON vp.sk_vendedor = v.sk_vendedor
ORDER BY vp.faturamento DESC;

-- PERGUNTA: quem e o top vendedor DENTRO de cada estado?
-- Isso NAO e possivel com GROUP BY simples — precisa de Window Function

-- RANK() OVER (PARTITION BY ... ORDER BY ...) 
-- = "rankeia cada linha dentro de um grupo (PARTITION BY)
--    ordenando por um criterio (ORDER BY)"
-- Equivalente Excel: nao existe formula simples — precisaria de PROCV aninhado
-- No SQL e uma linha so

WITH faturamento_vendedor AS (
    SELECT
        v.estado,
        v.seller_id,
        v.cidade,
        ROUND(SUM(f.valor_produto), 2) AS faturamento,
        COUNT(DISTINCT f.order_id)     AS total_pedidos
    FROM fato_pedidos f
    JOIN dim_vendedores v ON f.sk_vendedor = v.sk_vendedor
    WHERE f.status_pedido NOT IN ('canceled', 'unavailable')
    GROUP BY v.estado, v.seller_id, v.cidade
)
SELECT
    estado,
    seller_id,
    cidade,
    faturamento,
    total_pedidos,
    RANK() OVER (
        PARTITION BY estado    -- reinicia o ranking a cada estado
        ORDER BY faturamento DESC  -- criterio do ranking
    ) AS ranking_no_estado
FROM faturamento_vendedor
ORDER BY estado, ranking_no_estado;

-- PERGUNTA: qual foi o crescimento acumulado ao longo do tempo?
-- SUM() OVER (ORDER BY ...) = soma acumulada linha a linha
-- Nao precisa de GROUP BY — a Window Function faz isso internamente

WITH faturamento_mensal AS (
    SELECT
        t.ano,
        t.mes,
        t.nome_mes,
        ROUND(SUM(f.valor_produto), 2) AS faturamento_mes
    FROM fato_pedidos f
    JOIN dim_tempo t ON f.sk_tempo = t.sk_tempo
    WHERE f.status_pedido NOT IN ('canceled', 'unavailable')
    GROUP BY t.ano, t.mes, t.nome_mes
)
SELECT
    ano,
    mes,
    nome_mes,
    faturamento_mes,
    -- Soma acumulada: soma tudo desde a primeira linha ate a linha atual
    ROUND(SUM(faturamento_mes) OVER (
        ORDER BY ano, mes
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2) AS faturamento_acumulado,
    -- Variacao percentual em relacao ao mes anterior
    -- LAG() pega o valor da linha anterior
    ROUND(
        (faturamento_mes - LAG(faturamento_mes) OVER (ORDER BY ano, mes))
        / NULLIF(LAG(faturamento_mes) OVER (ORDER BY ano, mes), 0)
        * 100
    , 1) AS variacao_pct_mes_anterior
FROM faturamento_mensal
ORDER BY ano, mes;