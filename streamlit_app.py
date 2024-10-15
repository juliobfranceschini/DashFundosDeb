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

    # Certifique-se de que 'filtro_cnpj' seja definido antes de ser usado no merge
    # Exemplo: Aqui estamos filtrando por um CNPJ específico. Você pode permitir ao usuário selecionar um CNPJ.
    cnpj_especifico = '34.474.989/0001-97'  # Exemplo de CNPJ
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

        # Remover colunas específicas que você não deseja no arquivo final
        colunas_para_remover = ['Tipo Fundo', 'Percentual Aplicação', 'Tipo Aplicação', '% REUNE', 'Referência NTN-B',
                                'Intervalo indicativo mínimo', 'Intervalo indicativo máximo', 'Descrição Ativo', '% VNE']
        df_combinado = df_combinado.drop(columns=colunas_para_remover)

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
