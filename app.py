import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from os import listdir
from io import StringIO


st.set_page_config(
    page_title="Análise de dados",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
   
)

# st.title('Análise do Impacto do Clima na Produção/Exportação de Vinhos no Brasil')
st.header('Análise do Impacto do Clima na Produção/Exportação de Vinhos no Brasil', divider='rainbow')

"""
O propósito desses gráficos é de obter os dados de produção e exportação de vinhos, juntamente com as condições climáticas, e dessa forma analisar até que ponto uma condição climática em específico pode influenciar na produção, e consequentemente nos valores de exportação de vinhos do Brasil.
Fonte dos dados climáticos:
"""

arquivos_em = listdir('dados/metereologicos/')

dados_climaticos = pd.DataFrame()

for index, arquivo in enumerate(arquivos_em):   
    # criando uma string com o nome do número da estação metereologica
    estacao = arquivo[:11]; 
    
    # atribuindo a string a um nome de variável
    globals()[estacao] = pd.read_csv('dados/metereologicos/' + arquivo, sep=";", skiprows=10)
    
    # obtendo o nome da estacao na primeira linha do aquivo
    with open('dados/metereologicos/' + arquivo, 'r') as arquivo:
        for texto in arquivo.readlines():

            if (texto.startswith('Nome')):
                nome_estacao = texto[6:]

            if (texto.startswith('Codigo')):
                codigo_estacao = texto[16:]
                        
    # adicionando uma coluna com o nome da estacao    
    globals()[estacao].insert(1, 'DC_NOME', nome_estacao.replace('\n',''))
    globals()[estacao].insert(2, 'CD_ESTACAO', codigo_estacao.replace('\n',''))
    
    # consolidando todos os dados em um único dataframe
    dados_climaticos = pd.concat([dados_climaticos,globals()[estacao]])

# removendo colunas não utilizadas, e excluindo dados nulos
dados_climaticos.drop(['Unnamed: 1', 'Unnamed: 7'], axis=1, inplace=True)
dados_climaticos.dropna()

# Obtendo informações sobre as estacoes metereologicas:
# https://portal.inmet.gov.br/
estacoes_convencionais = pd.read_csv('dados/estacoes/CatalogoEstacoesAutomaticas.csv', sep=";")
estacoes_automaticas = pd.read_csv('dados/estacoes/CatalogoEstacoesConvencionais.csv', sep=";")
    
# criando coluna para identificar o tipo da estacao
estacoes_convencionais['TIPO'] = 'convencional'
estacoes_automaticas['TIPO'] = 'automatica'

# unindo os dados de todas as estacoes em um único dataframe
estacoes_operantes = pd.concat([estacoes_automaticas, estacoes_convencionais])

# filtrando somente as colunas necessárias
estacoes_operantes = estacoes_operantes[['DC_NOME', 'SG_ESTADO', 'CD_ESTACAO', 'TIPO']]


dados_climaticos['CD_ESTACAO'] = dados_climaticos['CD_ESTACAO'].astype('int64')

# fazendo um merge entre as estacoes operantes e os dados metereologicos
dados_consolidados = estacoes_operantes.merge(dados_climaticos,  how='inner', on='CD_ESTACAO')

dados_consolidados.dropna(inplace=True)

dados_consolidados.drop('DC_NOME_y', axis=1, inplace=True)
dados_consolidados.rename(columns={"DC_NOME_x":"DC_NOME"}) 

# renomeando colunas
dados_consolidados.columns = ['NM_ESTACAO', 'SG_UF_ESTADO', 'CD_ESTACAO', 'TP_ESTACAO', 'DT_MEDICAO',
       'NUMERO_DIAS_COM_PRECIP_PLUV',
       'PRECIPITACAO_TOTAL_EM_MILIMETROS',
       'TEMPERATURA_MAXIMA_MEDIA',
       'TEMPERATURA_MEDIA_COMPENSADA',
       'TEMPERATURA_MINIMA_MEDIA',
       'UMIDADE_RELATIVA_DO_AR_MEDIA_MENSAL_PORCENTAGEM']

# Converter a coluna DT_MEDICAO para tipo date
dados_consolidados['DT_MEDICAO'] = pd.to_datetime(dados_consolidados['DT_MEDICAO'])

# Criando a coluna ANO
dados_consolidados['ANO'] = dados_consolidados['DT_MEDICAO'].dt.year



# criando a coluna REGIAO
ufs_regiao = """Unidade federativa	Sigla	Região
Acre	AC	Região Norte
Alagoas	AL	Região Nordeste
Amapá	AP	Região Norte
Amazonas	AM	Região Norte
Bahia	BA	Região Nordeste
Ceará	CE	Região Nordeste
Distrito Federal	DF	Região Centro-Oeste
Espírito Santo	ES	Região Sudeste
Goiás	GO	Região Centro-Oeste
Maranhão	MA	Região Nordeste
Mato Grosso	MT	Região Centro-Oeste
Mato Grosso do Sul	MS	Região Centro-Oeste
Minas Gerais	MG	Região Sudeste
Pará	PA	Região Norte
Paraíba	PB	Região Nordeste
Paraná	PR	Região Sul
Pernambuco	PE	Região Nordeste
Piauí	PI	Região Nordeste
Rio de Janeiro	RJ	Região Sudeste
Rio Grande do Norte	RN	Região Nordeste
Rio Grande do Sul	RS	Região Sul
Rondônia	RO	Região Norte
Roraima	RR	Região Norte
Santa Catarina	SC	Região Sul
São Paulo	SP	Região Sudeste
Sergipe	SE	Região Nordeste
Tocantins	TO	Região Norte"""


# funcao para mapear a regiao
regioes_io = StringIO(ufs_regiao)
regioes = pd.read_csv(regioes_io, sep="\t")
ufs = list([regioes['Sigla']])
regiao = list([regioes['Região']])
dict_regiao = {}

for i in range(27):
    uf = ufs[0][i]
    reg = regiao[0][i]

    dict_regiao[uf] = reg


# criando o campo regiao mapeando a funcao acima
dados_consolidados['REGIAO'] = dados_consolidados['SG_UF_ESTADO'].map(dict_regiao)  

dados_agrupados_por_estados = dados_consolidados.groupby(by=['SG_UF_ESTADO','ANO']).mean(numeric_only=True).reset_index()
dados_agrupados_por_regiao = dados_consolidados.groupby(by=['SG_UF_ESTADO','REGIAO', 'ANO']).mean(numeric_only=True).reset_index()



tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Análise Climática", 
                                              "Chuva x Exportação", 
                                              "Temperatura Média x Exportação", 
                                              "Temperatura Minima x Exportação", 
                                              "Correlação entre as variáveis",
                                              "Mapa de Calor Correlação Spearman",
                                              "Mapa de Calor Correlação Pearson"])
# tab5, tab6, tab7, tab8, tab9 = st.tabs(["sadasdas", "Csadsado", "Tsdsadsadia x Exportação", "asdsdsado", "Deasdsadsad"])

    
# omite as mensagens de deprecated
st.set_option('deprecation.showPyplotGlobalUse', False)

with tab0:
    with st.container():
        st.write("### Análise da condição climática ao decorrer dos anos")

        with st.expander("Descrição da Análise"):
            st.write("""
                Nos gráficos abaixo estamos exibindo os gráficos das condições climáticas entre os anos de 2008 e 2022, como temperatura, precipitação, unidade relativa do ar,
                    quantidade de dias com chuva, entre outros. Essas informações nos darão uma base para comparar com a quantidade de exportação durante o mesmo período,
                    tendo a possibilidade de inferir se há ou não alguma correlação entre as variáveis.
                    
            """)    

        lista_estados = ['RS']
        dados_temperatura = dados_agrupados_por_estados.query('SG_UF_ESTADO == @lista_estados')[['ANO','TEMPERATURA_MEDIA_COMPENSADA','SG_UF_ESTADO']]
        dados_precipitacao = dados_agrupados_por_estados.query('SG_UF_ESTADO == @lista_estados')[['ANO','PRECIPITACAO_TOTAL_EM_MILIMETROS','SG_UF_ESTADO']]
        dados_umidade_relativa = dados_agrupados_por_estados.query('SG_UF_ESTADO == @lista_estados')[['ANO','UMIDADE_RELATIVA_DO_AR_MEDIA_MENSAL_PORCENTAGEM','SG_UF_ESTADO']]
        dados_numero_dias_com_precipitacao = dados_agrupados_por_estados.query('SG_UF_ESTADO == @lista_estados')[['ANO','NUMERO_DIAS_COM_PRECIP_PLUV','SG_UF_ESTADO']]
        lista_estados = ['RS']

        # definindo estrutura dos subplots
        fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(15,10))

        # Gráfico de temperatura média
        plt.ylim(0,40)
        axes[0,0].grid(linestyle="--", color = 'red')
        axes[0,0].set_ylabel('Temperatura Media')
        axes[0,0].set_xlabel('')
        sns.lineplot(ax = axes[0,0], data=dados_temperatura, x = 'ANO', y = 'TEMPERATURA_MEDIA_COMPENSADA', hue = 'SG_UF_ESTADO')
        axes[0,0].set_title("Temperatura Média")

        # Gráfico por precipitação
        plt.ylim(0,200)
        axes[0,1].grid(linestyle="--", color = 'red')
        axes[0,1].set_ylabel('Precipitação em MM')
        axes[0,1].set_xlabel('')
        sns.lineplot(ax = axes[0,1], data=dados_precipitacao, x = 'ANO', y = 'PRECIPITACAO_TOTAL_EM_MILIMETROS', hue = 'SG_UF_ESTADO')
        axes[0,1].set_title("Precipitação em MM -  Média")

        # Gráfico por umidade relativa do ar
        plt.ylim(0,200)
        plt.grid(linestyle="--", color = 'red')
        axes[1,0].grid(linestyle="--", color = 'red')
        axes[1,0].set_ylabel('Umidade do Ar')
        sns.lineplot(ax = axes[1,0], data=dados_umidade_relativa, x = 'ANO', y = 'UMIDADE_RELATIVA_DO_AR_MEDIA_MENSAL_PORCENTAGEM', hue = 'SG_UF_ESTADO')
        axes[1,0].set_title("Umidade Relativa do Ar")

        # Gráfico do número de dias com precipitação
        plt.ylim(0,50)
        axes[1,1].grid(linestyle="--", color = 'red')
        axes[1,1].set_ylabel('Umidade do Ar')
        sns.lineplot(ax = axes[1,1], data=dados_numero_dias_com_precipitacao, x = 'ANO', y = 'NUMERO_DIAS_COM_PRECIP_PLUV', hue = 'SG_UF_ESTADO')
        axes[1,1].set_title("Número de dias com precipitação")

        fig.tight_layout()
        st.pyplot()




with tab1:
    st.write("### Chuva x Exportação de vinhos ao decorrer dos anos")
    with st.expander("Descrição da Análise"):
        st.write("""
            Podemos observar abaixo, que a variação das linhas durante os anos entre os 2 gráficos, não tem similaridades. Dessa forma podemos inferir que a evolução ou declínio
                 do volume de chuva, não está relacionado ao volume de exportação durante os anos avaliados.
                 
        """)    


    # Exportação de vinhos
    # necessário rodar: pip install openpyxl
    dados_vinho = pd.read_excel('dados/data.xlsx', skipfooter=2)
    # dados_vinho

    # # Retirando a coluna Continent
    dados_vinho = dados_vinho.rename(columns={'Region/Country':'Country'})
    producao = dados_vinho.query('Variable == "Production"')
    exportacao = dados_vinho.query('Variable == "Exports"')

    figure, left_ax = plt.subplots(1,1)
    figure.subplots_adjust(right=1.50)
    sns.lineplot(data=exportacao.query('Country == "Brazil"'), x = 'Year', y = 'Quantity', color="red")

    left_ax.set_ylabel('Exportação')
    left_ax.set_xlabel('Ano')
    left_ax.legend(['Quantidade Exportada'], loc='upper left')
    left_ax.grid(linestyle=":", color = 'red')

    right_ax = left_ax.twinx()
    sns.lineplot(data=dados_precipitacao, x = 'ANO', y = 'PRECIPITACAO_TOTAL_EM_MILIMETROS', hue = 'SG_UF_ESTADO', color="blue")
    right_ax.set_ylabel('Precipitação em MM')
    right_ax.legend(['Precipitação em MM'])

    plt.title('Quantidade Exportada x Precipitação em MM')
    figure.tight_layout()
    st.pyplot(figure)




with tab2:
    st.write("### Comparativo entre Temperatura Média x Exportação de vinhos ao decorrer dos anos")
    with st.expander("Descrição da Análise"):
        st.write("""
            Podemos observar abaixo..........
                 
        """)    


    fig = plt.figure(figsize=(12,6))

    x = dados_temperatura['TEMPERATURA_MEDIA_COMPENSADA']
    y = dados_temperatura['ANO']

    w = exportacao.query('Country == "Brazil"')['Quantity']
    z = exportacao.query('Country == "Brazil"')['Year']

    axes1 = fig.add_axes([0.1, 0.1, 0.8, 0.8]) # eixos da figura principal
    axes2 = fig.add_axes([0.2, 0.50, 0.4, 0.3]) # eixos da figura secundária

    # Figura principal
    axes1.plot(y, x, 'r')
    axes1.set_xlabel('Ano')
    axes1.set_ylabel('Grau Celsius')
    axes1.set_title('Temperatura Média')

    # Figura secundária
    axes2.plot(z, w, 'g')
    axes2.set_xlabel('Ano')
    axes2.set_ylabel('hl')
    axes2.set_title('Quantidade Exportação');    

    st.pyplot(fig)

with tab3:
    st.write("### Comparativo entre Temperatura Mínima x Exportação")    

    with st.expander("Descrição da Análise"):
        st.write("""
            Podemos observar abaixo..........
                 
        """)    

    dados_temperatura_media =dados_temperatura_minima = dados_agrupados_por_estados.query('SG_UF_ESTADO == @lista_estados')[['ANO','TEMPERATURA_MINIMA_MEDIA','SG_UF_ESTADO']]


    # Dados
    x = dados_temperatura_minima['TEMPERATURA_MINIMA_MEDIA']
    y = dados_temperatura_minima['ANO']

    w = exportacao.query('Country == "Brazil"')['Quantity']
    z = exportacao.query('Country == "Brazil"')['Year']

    # Cria os subplots
    fig, axes = plt.subplots(1, 2, figsize = (12,4))
        
    # Cria o plot1
    axes[0].plot(y, x, 'r')
    axes[0].set_title("Média da Temperatura Mínima")

    # Cria o plot2
    axes[1].plot(z, w, 'g')
    # axes[1].set_yscale("log")
    axes[1].set_title("Exportação em hl");        
    st.pyplot()


with tab4:
    st.write("### Analisando a correlação entre as variáveis")

    with st.expander("Descrição da Análise"):
        st.write("""
            Podemos observar abaixo..........
                 
        """)    

    dados_exportacao_brasil = dados_vinho.query('Country == "Brazil" and Variable == "Exports"') 
    dados_climaticos_brasil = dados_agrupados_por_estados.query('SG_UF_ESTADO == "RS"')
    dados_exportacao_clima = dados_exportacao_brasil.merge(dados_climaticos_brasil, left_on='Year', right_on='ANO')
    dados_exportacao_clima.columns = ['CONTINENTE', 'PAIS', 'PRODUTO', 'VARIAVEL', 'ANO_', 'UNIDADE',
       'TOTAL_EXPORTADO', 'SG_UF_ESTADO', 'ANO', 'NUMERO_DIAS_COM_PRECIP_PLUV',
       'PRECIPITACAO_TOTAL_EM_MILIMETROS', 'TEMPERATURA_MAXIMA_MEDIA',
       'TEMPERATURA_MEDIA_COMPENSADA', 'TEMPERATURA_MINIMA_MEDIA',
       'UMIDADE_RELATIVA_DO_AR_MEDIA_MENSAL_PORCENTAGEM']
    
    dados_exportacao_clima_correlacao = dados_exportacao_clima[['TOTAL_EXPORTADO', 'NUMERO_DIAS_COM_PRECIP_PLUV',
       'PRECIPITACAO_TOTAL_EM_MILIMETROS', 'TEMPERATURA_MAXIMA_MEDIA',
       'TEMPERATURA_MEDIA_COMPENSADA', 'TEMPERATURA_MINIMA_MEDIA',
       'UMIDADE_RELATIVA_DO_AR_MEDIA_MENSAL_PORCENTAGEM']]
    
    sns.pairplot(dados_exportacao_clima_correlacao)
    st.pyplot()

with tab5:
    st.write("### Mapa de calor de correlação SPEARMAN")

    with st.expander("Descrição da Análise"):
        st.write("""
            Podemos observar abaixo..........
                 
        """)    


    correlacao = dados_exportacao_clima_correlacao.corr("spearman")
    ax = sns.heatmap(correlacao, annot = True, fmt=".1f", linewidths=.6)
    plt.title('Correlação entre Quantidade Exportada e Dados Climáticos')
    st.pyplot()

with tab6:
    st.write("### Mapa de calor de correlação SPEARMAN")

    with st.expander("Descrição da Análise"):
        st.write("""
            Podemos observar abaixo..........
                 
        """)    

    correlacao = dados_exportacao_clima_correlacao.corr("pearson")
    ax = sns.heatmap(correlacao, annot = True, fmt=".1f", linewidths=.6)
    plt.title('Correlação entre Quantidade Exportada e Dados Climáticos')
    st.pyplot()    