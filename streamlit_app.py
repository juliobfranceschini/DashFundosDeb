import streamlit as st
import pandas as pd
import re
import xlsxwriter

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
st.title("Análise de Debêntures e Fundos")

# Upload do arquivo Excel
uploaded_file = st.file_uploader("Carregar arquivo Excel com as debêntures", type=["xls", "xlsx"])

if uploaded_file is not None:
    # Carregar o arquivo Excel
    df = pd.read_excel(uploaded_file, skiprows=0)  # Ajuste o número de linhas que você deseja pular, se necessário

    # Ajustar as opções de exibição para ver todas as colunas
    pd.set_option("display.max_columns", None)  # Mostrar todas as colunas
    pd.set_option("display.expand_frame_repr", False)  # Evitar quebra de linha

    # Filtrar pela data de referência
    df = df[df['Data de referência'] == '11/10/2024']

    # Carregar o filtro de CNPJ e realizar o merge
    # Aqui você precisa fornecer o DataFrame 'filtro_cnpj' com os dados corretos de fundos, ou carregar ele também via upload
    # filtro_cnpj = seu_dataframe_de_fundos  # Este DataFrame deve conter o CNPJ e outros dados relevantes

    # Realizar o merge entre 'filtro_cnpj' e a planilha carregada
    df_combinado = pd.merge(filtro_cnpj, df, on='Código', how='inner')

    # Modificar a coluna 'Remuneração' para extrair os números
    df_combinado['Remuneração'] = df_combinado['Remuneração'].apply(extrair_numeros)

    # Remover colunas específicas que você não deseja no arquivo final
    colunas_para_remover = ['Tipo Fundo', 'Percentual Aplicação', 'Tipo Aplicação', '% REUNE', 'Referência NTN-B',
                            'Intervalo indicativo mínimo', 'Intervalo indicativo máximo', 'Descrição Ativo', '% VNE']
    df_combinado = df_combinado.drop(columns=colunas_para_remover)

    # Remover colunas que contenham apenas valores NaN ou apenas zeros
    df_combinado = df_combinado.dropna(axis=1, how='all')  # Remove colunas com todos os valores NaN
    df_combinado = df_combinado.loc[:, (df_combinado != 0).any(axis=0)]  # Remove colunas com todos os valores 0

    # Calcular o percentual de cada 'Valor Mercado Posição Final' com relação à soma total
    soma_valor_mercado = df_combinado['Valor Mercado Posição Final'].sum()
    df_combinado['% Valor Mercado'] = df_combinado['Valor Mercado Posição Final'] / soma_valor_mercado

    # Ordenar o DataFrame de forma decrescente com base na coluna 'Valor Mercado Posição Final'
    df_combinado = df_combinado.sort_values(by='Valor Mercado Posição Final', ascending=False)

    # Função para criar a tabela dinâmica (pivot table) com médias ponderadas
    def criar_pivot_table(df):
        pivot_table = df_combinado[df_combinado['Tipo Remuneração'].isin(['DI SPREAD', 'IPCA SPREAD', 'DI PERCENTUAL'])]

        # Criar a pivot table com médias ponderadas
        pivot_result = pivot_table.groupby('Tipo Remuneração').apply(
            lambda grupo: pd.Series({
                'Remuneração Média Ponderada': media_ponderada(grupo, 'Remuneração', '% Valor Mercado'),
                'Taxa Compra Média Ponderada': media_ponderada(grupo, 'Taxa de compra', '% Valor Mercado'),
                'Taxa Indicativa Média Ponderada': media_ponderada(grupo, 'Taxa indicativa', '% Valor Mercado'),
                'Duration Média Ponderada (anos)': media_ponderada(grupo, 'Duration', '% Valor Mercado') / 252,
            })
        ).reset_index()

        return pivot_result

    # Gerar a pivot table
    pivot_table = criar_pivot_table(df_combinado)

    # Exibir os dados no Streamlit
    st.write("### Dados Combinados das Debêntures:")
    st.dataframe(df_combinado)

    st.write("### Tabela Dinâmica com Médias Ponderadas:")
    st.dataframe(pivot_table)

    # Opção para exportar os resultados para Excel
    if st.button('Baixar resultado como Excel'):
        with pd.ExcelWriter('TaxaMédiaFundo.xlsx', engine='xlsxwriter') as writer:
            df_combinado.to_excel(writer, sheet_name='Dados', index=False)
            pivot_table.to_excel(writer, sheet_name='Pivot Table', index=False)

            # Acessar o workbook e worksheet
            workbook = writer.book
            worksheet = writer.sheets['Dados']
            worksheet_pivot = writer.sheets['Pivot Table']

            # Definir o formato de moeda (R$)
            currency_format = workbook.add_format({'num_format': 'R$ #,##0.00'})

            # Definir o formato de porcentagem (0.00%)
            percentage_format = workbook.add_format({'num_format': '0.00%'})

            # Aplicar o formato de moeda à coluna 'Valor Mercado Posição Final'
            valor_mercado_col_idx = df_combinado.columns.get_loc('Valor Mercado Posição Final')
            worksheet.set_column(valor_mercado_col_idx, valor_mercado_col_idx, None, currency_format)

            # Aplicar o formato de porcentagem à coluna 'Percentual Valor Mercado'
            percentual_col_idx = df_combinado.columns.get_loc('% Valor Mercado')
            worksheet.set_column(percentual_col_idx, percentual_col_idx, None, percentage_format)

        st.success('Arquivo Excel gerado com sucesso!')

else:
    st.write("Por favor, carregue um arquivo Excel para continuar.")

