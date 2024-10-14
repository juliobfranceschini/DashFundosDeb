import streamlit as st
import pandas as pd
import zipfile
import io
import requests
import re

# Função para carregar e concatenar os dados de fundos a partir de um arquivo ZIP da CVM
def carregar_dados_cvm(ano, mes):
    url = f'https://dados.cvm.gov.br/dados/FI/DOC/CDA/DADOS/cda_fi_{ano}{mes}.zip'
    response = requests.get(url)
    dataframes = []
    with zipfile.ZipFile(io.BytesIO(response.content), 'r') as arquivo_zip:
        for file_name in arquivo_zip.namelist():
            df = pd.read_csv(arquivo_zip.open(file_name), sep=';', encoding='ISO-8859-1')
            dataframes.append(df)
    dados_fundos_total = pd.concat(dataframes, ignore_index=True)
    return dados_fundos_total

# Função para carregar a planilha de debêntures
def carregar_planilha_debentures(uploaded_file):
    df = pd.read_excel(uploaded_file)
    return df

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

# Função para criar a pivot table com médias ponderadas
def criar_pivot_table(df):
    pivot_table = df[df['Tipo Remuneração'].isin(['DI SPREAD', 'IPCA SPREAD', 'DI PERCENTUAL'])]
    
    # Criar a pivot table com médias ponderadas
    pivot_result = pivot_table.groupby('Tipo Remuneração').apply(
        lambda grupo: pd.Series({
            'Média Ponderada Taxa de Compra': media_ponderada(grupo, 'Taxa de compra', '% Valor Mercado'),
            'Média Ponderada Taxa Indicativa': media_ponderada(grupo, 'Taxa indicativa', '% Valor Mercado'),
            'Média Ponderada Duration': media_ponderada(grupo, 'Duration', '% Valor Mercado')
        })
    ).reset_index()

    return pivot_result

# Título do dashboard
st.title("Dashboard de Fundos e Debêntures")

# Sidebar para os parâmetros de data dos fundos
st.sidebar.header("Parâmetros de Data - Fundos")
ano = st.sidebar.selectbox("Selecione o Ano:", ["2024", "2023"])
mes = st.sidebar.selectbox("Selecione o Mês:", ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"])

# Carregar os dados de fundos usando a função
dados_fundos_total = carregar_dados_cvm(ano, mes)

# Limpar e renomear colunas de fundos
dados_fundos_total = dados_fundos_total.rename(columns={
    'TP_FUNDO': 'Tipo Fundo',
    'CNPJ_FUNDO': 'CNPJ Fundo',
    'DENOM_SOCIAL': 'Denominação Social',
    'VL_MERC_POS_FINAL': 'Valor Mercado Posição Final',
    'VL_PATRIM_LIQ': 'Patrimônio Líquido'
})

# Ajustar colunas
dados_fundos_total['Percentual Aplicação'] = (dados_fundos_total['Valor Mercado Posição Final'] /
                                              dados_fundos_total['Patrimônio Líquido']) * 100

# Criar filtros no dashboard para o usuário escolher os fundos
st.sidebar.header("Filtros - Fundos")
cnpj_filtro = st.sidebar.text_input("Filtrar por CNPJ do Fundo:")
tipo_aplicacao_filtro = st.sidebar.multiselect("Filtrar por Tipo de Aplicação:",
                                               options=dados_fundos_total['Tipo Aplicação'].unique())

# Aplicar os filtros nos fundos
dados_filtrados = dados_fundos_total

if cnpj_filtro:
    dados_filtrados = dados_filtrados[dados_filtrados['CNPJ Fundo'] == cnpj_filtro]

if tipo_aplicacao_filtro:
    dados_filtrados = dados_filtrados[dados_filtrados['Tipo Fundo'].isin(tipo_aplicacao_filtro)]

# Exibir os dados filtrados
st.write("### Dados de Fundos Filtrados:")
st.dataframe(dados_filtrados)

# Se a base de debêntures for carregada, exibir os dados relacionados
st.sidebar.header("Carregar Dados de Debêntures")
uploaded_file = st.sidebar.file_uploader("Carregar arquivo Excel de Debêntures", type="xls")

if uploaded_file is not None:
    # Carregar a planilha de debêntures
    df_debentures = carregar_planilha_debentures(uploaded_file)
    
    # Entrada para o código da debênture
    codigo_debenture = st.text_input("Digite o Código da Debênture:", "")
    
    # Se um código foi inserido, filtrar os dados de debêntures
    if codigo_debenture:
        df_filtrado = df_debentures[df_debentures['Código'] == codigo_debenture]
        
        if not df_filtrado.empty:
            data_disponivel = st.selectbox("Selecione a Data de Referência:", df_filtrado['Data de referência'].unique())
            debenture_dados = df_filtrado[df_filtrado['Data de referência'] == data_disponivel]

            if not debenture_dados.empty:
                st.write(f"### Informações da Debênture ({codigo_debenture}) em {data_disponivel}:")

                # Ajustar a coluna 'Duration' para mostrar o valor em anos
                debenture_dados['Duration (em anos)'] = debenture_dados['Duration'] / 252

                # Exibir as colunas relevantes (incluindo a nova coluna 'Duration (em anos)')
                st.write(debenture_dados[['Remuneração', 'Tipo Remuneração', 'Taxa de compra', 'Duration (em anos)']])
                
                # Gerar a pivot table e exibir
                debenture_dados['% Valor Mercado'] = debenture_dados['Valor Mercado Posição Final'] / debenture_dados['Valor Mercado Posição Final'].sum()
                pivot_table = criar_pivot_table(debenture_dados)
                st.write("### Tabela Dinâmica - Médias Ponderadas")
                st.dataframe(pivot_table)
            else:
                st.write("Nenhuma informação disponível para essa combinação de código e data.")
        else:
            st.write("Nenhuma debênture encontrada com o código fornecido.")
else:
    st.write("Por favor, carregue um arquivo Excel de debêntures para buscar as informações.")
