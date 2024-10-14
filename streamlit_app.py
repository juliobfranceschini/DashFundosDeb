import streamlit as st
import pandas as pd
import requests
import zipfile
import io
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

# Função para carregar dados da CVM (arquivo ZIP) e gerar o DataFrame
def carregar_dados_cvm(ano, mes):
    url = f'https://dados.cvm.gov.br/dados/FI/DOC/CDA/DADOS/cda_fi_{ano}{mes}.zip'
    response = requests.get(url)
    dataframes = []
    
    with zipfile.ZipFile(io.BytesIO(response.content), 'r') as arquivo_zip:
        for file_name in arquivo_zip.namelist():
            df = pd.read_csv(arquivo_zip.open(file_name), sep=';', encoding='ISO-8859-1')
            dataframes.append(df)
    
    dados_fundos_total = pd.concat(dataframes, ignore_index=True)
    
    # Renomear colunas e ajustar os dados
    dados_fundos_total = dados_fundos_total.rename(columns={
        'TP_FUNDO': 'Tipo Fundo',
        'CNPJ_FUNDO': 'CNPJ Fundo',
        'DENOM_SOCIAL': 'Denominação Social',
        'DT_COMPTC': 'Data Competência',
        'ID_DOC': 'ID Documento',
        'VL_PATRIM_LIQ': 'Patrimônio Líquido',
        'TP_APLIC': 'Tipo Aplicação',
        'TP_ATIVO': 'Tipo Ativo',
        'CD_ATIVO': 'Código',
        'DS_ATIVO': 'Descrição Ativo',
        'VL_MERC_POS_FINAL': 'Valor Mercado Posição Final'
    })

    # Remover colunas que não são necessárias
    colunas_para_remover = ['Quantidade Venda Negociada', 'Quantidade Aquisição Negociada', 'Emissor Ligado', 'Tipo Negociação']
    dados_fundos_total = dados_fundos_total.drop(columns=colunas_para_remover)
    
    return dados_fundos_total

# Função para filtrar dados por CNPJ
def filtrar_por_cnpj(dados_fundos_total, cnpj_fundo):
    filtro_cnpj = dados_fundos_total[dados_fundos_total['CNPJ Fundo'] == cnpj_fundo]
    
    if not filtro_cnpj.empty:
        # Calcular o percentual de cada 'Valor Mercado Posição Final'
        soma_valor_mercado = filtro_cnpj['Valor Mercado Posição Final'].sum()
        filtro_cnpj['% Valor Mercado'] = (filtro_cnpj['Valor Mercado Posição Final'] / soma_valor_mercado) * 100

    return filtro_cnpj

# Função para criar a pivot table com médias ponderadas
def criar_pivot_table(df):
    pivot_table = df[df['Tipo Aplicação'].isin(['DI SPREAD', 'IPCA SPREAD', 'DI PERCENTUAL'])]
    
    # Criar a pivot table com médias ponderadas
    pivot_result = pivot_table.groupby('Tipo Aplicação').apply(
        lambda grupo: pd.Series({
            'Média Ponderada Taxa de Compra': media_ponderada(grupo, 'Taxa de compra', '% Valor Mercado'),
            'Média Ponderada Taxa Indicativa': media_ponderada(grupo, 'Taxa indicativa', '% Valor Mercado'),
            'Média Ponderada Duration': media_ponderada(grupo, 'Duration', '% Valor Mercado')
        })
    ).reset_index()

    return pivot_result

# Título do dashboard
st.title("Dashboard de Fundos - CVM")

# Input para selecionar o ano e o mês
ano = st.sidebar.selectbox("Selecione o Ano", ["2024", "2023"])
mes = st.sidebar.selectbox("Selecione o Mês", [f'{i:02}' for i in range(1, 13)])

# Botão para carregar dados
if st.sidebar.button("Carregar Dados"):
    dados_fundos_total = carregar_dados_cvm(ano, mes)
    st.write("Dados carregados com sucesso!")

    # Input para o CNPJ do fundo
    cnpj_fundo = st.text_input("Digite o CNPJ do Fundo (com formatação):", "")

    if cnpj_fundo:
        dados_filtrados = filtrar_por_cnpj(dados_fundos_total, cnpj_fundo)

        # Verificar se há dados para o CNPJ fornecido
        if not dados_filtrados.empty:
            st.write(f"### Informações do Fundo ({cnpj_fundo}):")
            st.dataframe(dados_filtrados)

            # Gerar e exibir a pivot table
            pivot_table = criar_pivot_table(dados_filtrados)
            st.write("### Pivot Table - Médias Ponderadas:")
            st.dataframe(pivot_table)
        else:
            st.write(f"Nenhum fundo encontrado para o CNPJ: {cnpj_fundo}.")
