import streamlit as st
import pandas as pd
import xlsxwriter
import re

# Função para extrair apenas os números da coluna "Remuneração"
def extrair_numeros(remuneracao):
    match = re.findall(r"[-+]?\d*\.\d+|\d+", remuneracao.replace(',', '.'))
    if match:
        return float(match[0])
    else:
        return None

# Função para calcular a média ponderada
def media_ponderada(grupo, valor_col, peso_col):
    return (grupo[valor_col] * grupo[peso_col]).sum() / grupo[peso_col].sum()

# Título do Dashboard
st.title("Dashboard de Debêntures")

# Upload do arquivo Excel
uploaded_file = st.file_uploader("Carregar arquivo Excel", type=["xls", "xlsx"])

if uploaded_file is not None:
    # Carregar o DataFrame a partir do arquivo Excel
    df = pd.read_excel(uploaded_file)

    # Renomear as colunas com novos nomes mais descritivos
    df = df.rename(columns={
        'TP_FUNDO': 'Tipo Fundo',
        'CNPJ_FUNDO': 'CNPJ Fundo',
        'DENOM_SOCIAL': 'Denominação Social',
        'DT_COMPTC': 'Data Competência',
        'ID_DOC': 'ID Documento',
        'VL_PATRIM_LIQ': 'Patrimônio Líquido',
        'TP_APLIC': 'Tipo Aplicação',
        'TP_ATIVO': 'Tipo Ativo',
        'EMISSOR_LIGADO': 'Emissor Ligado',
        'TP_NEGOC': 'Tipo Negociação',
        'QT_VENDA_NEGOC': 'Quantidade Venda Negociada',
        'VL_VENDA_NEGOC': 'Valor Venda Negociada',
        'QT_AQUIS_NEGOC': 'Quantidade Aquisição Negociada',
        'VL_AQUIS_NEGOC': 'Valor Aquisição Negociada',
        'QT_POS_FINAL': 'Quantidade Posição Final',
        'VL_MERC_POS_FINAL': 'Valor Mercado Posição Final',
        'VL_CUSTO_POS_FINAL': 'Valor Custo Posição Final',
        'DT_CONFID_APLIC': 'Data Confidencial Aplicação',
        'CD_ATIVO': 'Código',
        'DS_ATIVO': 'Descrição Ativo',
        'DT_VENC': 'Data Vencimento',
        'PF_PJ_EMISSOR': 'Pessoa Física/Jurídica Emissor',
        'CPF_CNPJ_EMISSOR': 'CPF/CNPJ Emissor',
        'EMISSOR': 'Emissor',
        'RISCO_EMISSOR': 'Risco Emissor',
        'CD_SELIC': 'Código Selic',
        'DT_INI_VIGENCIA': 'Data Início Vigência',
        'CD_PAIS': 'Código País',
        'PAIS': 'País',
        'CD_BV_MERC': 'Código BV Mercado',
        'BV_MERC': 'BV Mercado',
        'TP_TITPUB': 'Tipo Título Público',
        'CD_ISIN': 'Código ISIN',
        'DT_EMISSAO': 'Data Emissão',
        'CNPJ_FUNDO_COTA': 'CNPJ Fundo Cota',
        'NM_FUNDO_COTA': 'Nome Fundo Cota',
        'CD_SWAP': 'Código Swap',
        'DS_SWAP': 'Descrição Swap',
        'DT_FIM_VIGENCIA': 'Data Fim Vigência',
        'CNPJ_EMISSOR': 'CNPJ Emissor',
        'TITULO_POSFX': 'Título Pós-Fixado',
        'CD_INDEXADOR_POSFX': 'Código Indexador Pós-Fixado',
        'DS_INDEXADOR_POSFX': 'Descrição Indexador Pós-Fixado',
        'PR_INDEXADOR_POSFX': 'Percentual Indexador Pós-Fixado',
        'PR_CUPOM_POSFX': 'Percentual Cupom Pós-Fixado',
        'PR_TAXA_PREFX': 'Percentual Taxa Pré-Fixada',
        'AG_RISCO': 'Agência de Risco',
        'DT_RISCO': 'Data Risco',
        'GRAU_RISCO': 'Grau de Risco',
        'TITULO_CETIP': 'Título Cetip',
        'TITULO_GARANTIA': 'Título Garantia',
        'CNPJ_INSTITUICAO_FINANC_COOBR': 'CNPJ Instituição Financeira Coobrigada',
        'INVEST_COLETIVO': 'Investimento Coletivo',
        'INVEST_COLETIVO_GESTOR': 'Gestor Investimento Coletivo',
        'CD_ATIVO_BV_MERC': 'Código Ativo BV Mercado',
        'DS_ATIVO_EXTERIOR': 'Descrição Ativo Exterior',
        'QT_ATIVO_EXTERIOR': 'Quantidade Ativo Exterior',
        'VL_ATIVO_EXTERIOR': 'Valor Ativo Exterior'
    })

    # Excluir colunas específicas que você não deseja manter
    colunas_para_excluir = [
        'Quantidade Venda Negociada', 'Quantidade Aquisição Negociada', 'Quantidade Posição Final',
        'Quantidade Ativo Exterior', 'Emissor Ligado', 'Tipo Negociação', 'Valor Aquisição Negociada',
        'Valor Venda Negociada', 'Data Confidencial Aplicação', 'Risco Emissor', 'Código Selic', 
        'Data Início Vigência', 'Código ISIN', 'Data Fim Vigência'
    ]
    
    # Remover as colunas indesejadas
    df = df.drop(columns=colunas_para_excluir)

    # Exibir todas as colunas do DataFrame para ajudar na identificação
    st.write("Colunas disponíveis no arquivo:")
    st.write(df.columns)

    # Certifique-se de que 'filtro_cnpj' seja definido antes de ser usado no merge
    # Exemplo: Aqui estamos filtrando por um CNPJ específico. Você pode permitir ao usuário selecionar um CNPJ.
    cnpj_especifico = '34.474.989/0001-97'  # Exemplo de CNPJ

    # Verifique se a coluna "CNPJ Fundo" existe no DataFrame antes de usá-la
    if 'CNPJ Fundo' in df.columns:
        filtro_cnpj = df[df['CNPJ Fundo'] == cnpj_especifico]

        # Verifique se o 'filtro_cnpj' tem dados antes de fazer o merge
        if not filtro_cnpj.empty:
            # Filtrar pela data de referência
            df_filtrado = df[df['Data de referência'] == '11/10/2024']

            # Realizar o merge entre 'filtro_cnpj' e a 'planilha' pelo código
            df_combinado = pd.merge(filtro_cnpj, df_filtrado, on='Código', how='inner')

            # Modificar a coluna 'Remuneração' para extrair os números
            df_combinado['Remuneração'] = df_combinado['Remuneração'].apply(extrair_numeros)

            # Continuar com a lógica de remover colunas, cálculo de percentual e ordenação

            # Remover colunas que contenham apenas valores NaN ou apenas zeros
            df_combinado = df_combinado.dropna(axis=1, how='all')
            df_combinado = df_combinado.loc[:, (df_combinado != 0).any(axis=0)]

            # Calcular o percentual de cada 'Valor Mercado Posição Final' com relação à soma total
            soma_valor_mercado = df_combinado['Valor Mercado Posição Final'].sum()
            df_combinado['% Valor Mercado'] = df_combinado['Valor Mercado Posição Final'] / soma_valor_mercado

            # Ordenar o DataFrame de forma decrescente com base na coluna 'Valor Mercado Posição Final'
            df_combinado = df_combinado.sort_values(by='Valor Mercado Posição Final', ascending=False)

            # Exibir o DataFrame no Streamlit
            st.write("### Dados Filtrados:")
            st.dataframe(df_combinado)

        else:
            st.write("Nenhum fundo com o CNPJ especificado foi encontrado.")
    else:
        st.write("A coluna 'CNPJ Fundo' não foi encontrada no arquivo.")
