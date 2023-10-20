import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from os import listdir
from io import StringIO
import plotly.express as px
import requests

# configurando a páigna

st.set_page_config(
    page_title="Análise de dados",
    page_icon="🧊",
    layout="wide"
)

st.title(':rain_cloud: :sun_with_face: ANÁLISE DO IMPACTO DO CLIMA NA EXPORTAÇÃO DE VINHO :tornado_cloud: :thermometer:')

#### obtendo dados de geolocalizacao
url = 'https://labdados.com/produtos'
response = requests.get(url)
geo_localizacao = pd.DataFrame.from_dict(response.json())
geo_localizacao = geo_localizacao[['Local da compra', 'lat', 'lon']].drop_duplicates().sort_values(by='Local da compra')
geo_localizacao = geo_localizacao.rename(columns={'Local da compra': 'UF'})
geo_localizacao = geo_localizacao.set_index('UF')

#### obtendo dados de exportação por estado
dados_exportacao = pd.read_csv('dados/_EXP_2023.csv', sep=',')
exp_2023 = dados_exportacao.groupby(['CO_ANO', 'SG_UF_NCM']).sum().reset_index()
exp_2023_geo = exp_2023.merge(geo_localizacao, left_on='SG_UF_NCM', right_index=True)


#### obtendo dados das estações climáticas
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


# Obtendo dados da exportação / produção de vinhos
dados_vinho = pd.read_excel('dados/data.xlsx', skipfooter=2, engine='openpyxl')

# necessário rodar: pip install openpyxl
dados_vinho = pd.read_excel('dados/data.xlsx', skipfooter=2, engine='openpyxl')
dados_vinho = dados_vinho.rename(columns={'Region/Country':'Country'})
producao = dados_vinho.query('Variable == "Production"')
exportacao = dados_vinho.query('Variable == "Exports"')


# definindo graficos dos dados climaticos

lista_estados = ['RS']
dados_temperatura_media = dados_agrupados_por_estados.query('SG_UF_ESTADO == @lista_estados')[['ANO','TEMPERATURA_MEDIA_COMPENSADA','SG_UF_ESTADO']]
dados_temperatura_minima = dados_agrupados_por_estados.query('SG_UF_ESTADO == @lista_estados')[['ANO','TEMPERATURA_MINIMA_MEDIA','SG_UF_ESTADO']]
dados_temperatura_maxima = dados_agrupados_por_estados.query('SG_UF_ESTADO == @lista_estados')[['ANO','TEMPERATURA_MAXIMA_MEDIA','SG_UF_ESTADO']]
dados_precipitacao = dados_agrupados_por_estados.query('SG_UF_ESTADO == @lista_estados')[['ANO','PRECIPITACAO_TOTAL_EM_MILIMETROS','SG_UF_ESTADO']]
dados_umidade_relativa = dados_agrupados_por_estados.query('SG_UF_ESTADO == @lista_estados')[['ANO','UMIDADE_RELATIVA_DO_AR_MEDIA_MENSAL_PORCENTAGEM','SG_UF_ESTADO']]

# analise de correlação
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






# criando gráficos


fig_scatter_exportacao_temperatura_media = px.scatter(dados_exportacao_clima_correlacao,
                                                      x = 'TOTAL_EXPORTADO',
                                                      y = 'TEMPERATURA_MEDIA_COMPENSADA',
                                                      title= 'Dispersão Exportação x Temperatura Média')

fig_scatter_exportacao_temperatura_maxima = px.scatter(dados_exportacao_clima_correlacao,
                                                      x = 'TOTAL_EXPORTADO',
                                                      y = 'TEMPERATURA_MAXIMA_MEDIA',
                                                      title= 'Dispersão Exportação x Temperatura Máxima')

fig_scatter_exportacao_temperatura_minima = px.scatter(dados_exportacao_clima_correlacao,
                                                      x = 'TOTAL_EXPORTADO',
                                                      y = 'TEMPERATURA_MINIMA_MEDIA',
                                                      title= 'Dispersão Exportação x Temperatura Mínima')

fig_scatter_exportacao_umidade = px.scatter(dados_exportacao_clima_correlacao,
                                                      x = 'TOTAL_EXPORTADO',
                                                      y = 'UMIDADE_RELATIVA_DO_AR_MEDIA_MENSAL_PORCENTAGEM',
                                                      title= 'Dispersão Exportação x Umidade Relativa do Ar')


fig_scatter_exportacao_precipitacao = px.scatter(dados_exportacao_clima_correlacao,
                                                      x = 'TOTAL_EXPORTADO',
                                                      y = 'PRECIPITACAO_TOTAL_EM_MILIMETROS',
                                                      title= 'Dispersão Exportação x Preipitação')



fig_temperatura_media = px.line(dados_temperatura_media, 
                                x = 'ANO', 
                                y = 'TEMPERATURA_MEDIA_COMPENSADA',
                                range_y=(0,40),
                                # markers=True,
                                # color="ANO",
                                # line_dash='ANO',
                                title="Temperatura Média Compensada")

fig_temperatura_minima = px.line(dados_temperatura_minima, 
                                x = 'ANO', 
                                y = 'TEMPERATURA_MINIMA_MEDIA',
                                range_y=(0,40),
                                # markers=True,
                                # color="ANO",
                                # line_dash='ANO',
                                title="Temperatura Miníma (Média)")

fig_temperatura_maxima = px.line(dados_temperatura_maxima, 
                                x = 'ANO', 
                                y = 'TEMPERATURA_MAXIMA_MEDIA',
                                range_y=(0,40),
                                # markers=True,
                                # color="ANO",
                                # line_dash='ANO',
                                title="Temperatura Máxima (Média)")


fig_precipitacao = px.line(dados_precipitacao, 
                           x = 'ANO', 
                           y = 'PRECIPITACAO_TOTAL_EM_MILIMETROS',
                           title="Precipitação MM")

fig_umidade = px.line(dados_umidade_relativa, 
                      x = 'ANO', 
                      y = 'UMIDADE_RELATIVA_DO_AR_MEDIA_MENSAL_PORCENTAGEM',
                      title="Umidade Relativa do Ar")


fig_exportacao_precipitacao = px.line(exportacao.query('Country == "Brazil"'), 
                                      x = 'Year', 
                                      y = 'Quantity',
                                      title="Total Exportado")

fig_precipitacao_exportacao = px.line(dados_precipitacao, 
                                      x = 'ANO', 
                                      y = 'PRECIPITACAO_TOTAL_EM_MILIMETROS',
                                      title="Precipitação")

correlacao = dados_exportacao_clima_correlacao.corr("pearson")
fig_correlacao = px.imshow(correlacao, text_auto=True, aspect="auto")


# criando abas no dashboard
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs(['Geolocalização', 'Dados Climáticos', 'Exportação x Dados Climáticos', 'Dispersão', 'Correlação', 'Conclusão'])

with aba1:
   

    with st.container():
        st.write("### Estados exportadores de vinho no Brasil")

        with st.expander("Descrição da Análise"):
            st.write("""Para se analisar o impacto do clima na produção e exportação de vinho no Brasil,
                     primeiramente temos que encontrar qual estado é o maior produtor e exportador, e a partir
                     dessa análise, podemos avaliar como o clima influencia nesse estado. Nos gráficos 
                     abaixo, podemos observar que vários estados brasileiros produzem e exportam vinhos, mas o
                     Rio Grande do Sul é o responsável pela maioria das produções. Portanto, vamos nos basear
                     em como a interferência do clima altera ou não a produção e exportação desse estado.""")    
            
        qtd_estados = st.number_input('Quantidade de Estados Apresentados nos Gráficos', 2, 10, 3)        

    coluna1,coluna2 = st.columns(2)

    fig_mapa_exportacao_quantidade = px.scatter_geo(exp_2023_geo.sort_values(by='KG_LIQUIDO', ascending=False).head(qtd_estados),
                                    lat='lat',
                                    lon='lon',
                                    scope='south america',
                                    size='KG_LIQUIDO',
                                    template='seaborn',
                                    hover_name='SG_UF_NCM',
                                    hover_data={'lat':True, 'lon':True},
                                    color = "SG_UF_NCM",  
                                    title=f'Top {qtd_estados} dos Estados Exportadores de Vinho - KG LIQUIDO')




    fig_mapa_exportacao = px.scatter_geo(exp_2023_geo,
                                    lat='lat',
                                    lon='lon',
                                    scope='south america',
                                    template='seaborn',
                                    hover_name='SG_UF_NCM',
                                    hover_data={'lat':True, 'lon':True},
                                    color = "SG_UF_NCM",  
                                    title='Estados Exportadores de Vinho')



    fig_mapa_exportacao_quantidade_pizza = px.pie(exp_2023_geo.sort_values(by='KG_LIQUIDO', ascending=False).head(qtd_estados),
                                                labels='SG_UF_NCM',
                                                values='KG_LIQUIDO',
                                                title=f'Top {qtd_estados} dos Estados Exportadores de Vinho - KG LIQUIDO'
   
                                               )

    fig_mapa_exportacao_quantidade_pizza.update_layout(
                                                    paper_bgcolor='rgb(248, 248, 255)',
                                                    plot_bgcolor='rgb(248, 248, 255)',) 


    fig_mapa_exportacao_quantidade_bar = px.bar(exp_2023_geo.sort_values(by='KG_LIQUIDO', ascending=False).head(qtd_estados),
                                                y='SG_UF_NCM',
                                                x='KG_LIQUIDO',
                                                orientation='h',
                                                hover_data='KG_LIQUIDO',
                                                title=f'Top {qtd_estados} dos Estados Exportadores de Vinho - KG LIQUIDO'
                                                )
    fig_mapa_exportacao_quantidade_bar.update_layout(xaxis = dict(showgrid=True, showline=True),
                                                    yaxis = dict(showgrid=True, showline=True),
                                                    barmode='stack',
                                                    paper_bgcolor='rgb(248, 248, 255)',
                                                    plot_bgcolor='rgb(248, 248, 255)',) 


 
    with coluna1:
        st.plotly_chart(fig_mapa_exportacao, use_container_width=True)
        st.plotly_chart(fig_mapa_exportacao_quantidade_pizza, use_container_width=True)

    with coluna2:
        st.plotly_chart(fig_mapa_exportacao_quantidade, use_container_width=True)
        st.plotly_chart(fig_mapa_exportacao_quantidade_bar, use_container_width=True)


with aba2:
    with st.container():
        st.write("### Análise da condição climática no Rio Grande do Sul")

        with st.expander("Descrição da Análise"):
            st.write("""
                Abaixo estamos exibindo os gráficos das condições climáticas entre os anos de 2008 e 2022, como temperatura media, temperatura mínima, temperatura máxima, precipitação, unidade relativa do ar,
                    e umidade relativa do ar. Essas informações serão de suma importância na análise do impacto do clima,
                    tendo a possibilidade de inferir se há ou não alguma correlação entre as variáveis climáticas e números de exportação.
                    As informações, foram coletadas no site do imnpe, obtendo dados de todas das estações climáticas, desde 2008 até o ano de 2022, num total de 350 estações (convencionais e automáticas). """)    
    coluna1, coluna2 = st.columns(2)

    with coluna1:
        st.plotly_chart(fig_temperatura_media, use_container_width=True)
        st.plotly_chart(fig_temperatura_minima, use_container_width=True)
        st.plotly_chart(fig_temperatura_maxima, use_container_width=True)

    with coluna2:
        st.plotly_chart(fig_umidade, use_container_width=True)
        st.plotly_chart(fig_precipitacao, use_container_width=True)


with aba3:
    with st.container():
        st.write("### Comparativo Total Exportação x Dados Climáticos")

    with st.expander("Descrição da Análise"):
        st.write("""
                Abaixo estamos exibindo um comparativo entre os gráficos das variações climáticas e  os
                 gráficos dos valores das exportações de vinho, lado a lado. Percebe-se que visualmente não há semelhança
                 aparente, o que nos leva a uma hipótese que não há qualquer relação entre as variáveis.""")    

    coluna1, coluna2 = st.columns(2)

    with coluna1:
        st.plotly_chart(fig_exportacao_precipitacao, use_container_width=True)
        st.plotly_chart(fig_exportacao_precipitacao, use_container_width=True)
        st.plotly_chart(fig_exportacao_precipitacao, use_container_width=True)
        st.plotly_chart(fig_exportacao_precipitacao, use_container_width=True)
        st.plotly_chart(fig_exportacao_precipitacao, use_container_width=True)

    with coluna2:
        st.plotly_chart(fig_precipitacao, use_container_width=True)
        st.plotly_chart(fig_temperatura_maxima, use_container_width=True)
        st.plotly_chart(fig_temperatura_minima, use_container_width=True)
        st.plotly_chart(fig_temperatura_media, use_container_width=True)
        st.plotly_chart(fig_umidade, use_container_width=True)


with aba4:
    with st.container():
        st.write("### Comparativo Exportação x Dados Climáticos")

    with st.expander("Descrição da Análise"):
        st.write("""
                Abaixo estamos exibindo um gráfico de dispersão entre as variáveis climáticas e os valores
                 exportados. Percebemos claramente que não há nenhum padrão ou tendências nessa relação
                 em nenhuma das variáveis climáticas analisadas, o que nos leva a levantar a hipótese que 
                 realmente não há relação entre as variáveis.""")    

    coluna1, coluna2 = st.columns(2)

    with coluna1:
        st.plotly_chart(fig_scatter_exportacao_temperatura_media, use_container_width=True)
        st.plotly_chart(fig_scatter_exportacao_temperatura_minima, use_container_width=True)
        st.plotly_chart(fig_scatter_exportacao_temperatura_maxima, use_container_width=True)

    with coluna2:
        st.plotly_chart(fig_scatter_exportacao_umidade, use_container_width=True)
        st.plotly_chart(fig_scatter_exportacao_precipitacao, use_container_width=True)
            


with aba5:
    with st.container():
        st.write("### Correlação entre os dados climáticos o de exportação de vinho")

    with st.expander("Descrição da Análise"):
        st.write("""
                Abaixo estamos exibindo um gráfico com mapa de calor que exibe a correlação entre os dados climáticos
                 e os valores exportados no estado do Rio Grande do Sul. Podemos observar na primeira linha ou primeira coluna, a baixa correlação entre
                 essas variáveis, o que confirma nossa hipótese de não haver influência específica do clima na exportação e 
                 produção de vinho.""")    

    st.plotly_chart(fig_correlacao, use_container_width=True)
    
with aba6:
     with st.container():    
        st.markdown("""
            # Conclusão

            Fundamentado nas informações coletadas a respeito do que foi proposto nos objetivos deste estudo, chegou-se às seguintes conclusões.

            * Não é apenas um fator climático isolado que impacta na produção e exportação de vinhos;
            * As variáveis analisadas isoladamente, não tem correlação com a exportação;
            * Gráficos de dispersão apresentados, confirmam nossas hipóteses;
            * As características do terroir dão a cada vinho aromas, sabores e colorações únicos, sendo que o clima é apenas uma parte dessa contribuição, porém muito importante no processo de produção da bebida. 

            * Falar de terroir é falar de um conjunto de fatores como:
                * Topografia;
                * Geologia;
                * Pedologia (estudo do solo);
                * Drenagem;
                * Clima e microclima;
                * Castas (categorias);
                * Intervenção humana;
                * Cultura, história e tradição.

            ## Então como o clima influencia na produção e característica do vinho?

            Os meteorologistas definem o clima e seus componentes como os parâmetros e variações de: temperatura, precipitações (chuva, neve, granizo) e massas de ar de um lugar determinado. Estes dependem da proximidade do trópico ou círculo polar, além da presença de massas de água (como mares, lagos e rios) ou barreiras de ar (cordilheiras). 

            ## :red[Portanto, as características do terroir determinam a qualidade na produção do vinho, sendo que o clima é apenas uma parte dessa contribuição, porém muito importante no processo de produção da bebida.]  ##

            No mundo do vinho falamos de vinhos de clima frio ou clima quente. É uma generalização, porém permite realizar comparações. Anotem: a geologia e o solo do vinhedo não são tão decisivos quanto as diferenças climáticas. A geologia, mais que tudo, é responsável pelas expressões sutis nas características dos vinhos dentro de um mesmo clima ou região.

            As influências climáticas de uma zona influem em grande parte no tipo de variedades que serão cultivadas, mas também no tipo de práticas vitivinícolas. As parreiras pedem a presença de sol, calor e água para seu desenvolvimento saudável. Além disso, a luz (a quantidade de dias ensolarados durante o ano) influi inclusive sobre a latência que se produz após a colheita, quando a videira essencialmente se fecha e reserva sua energia para o começo do ciclo de crescimento do próximo ano.

            De igual importância é a quantidade de chuva (e a necessidade de irrigação complementar). Em média, uma videira necessita em torno de 710 mm de água para o sustento durante a temporada de crescimento. No Mediterrâneo e em muitos climas continentais, o clima durante a estação de crescimento pode ser bastante seco e requer irrigação adicional.

            Outros fatores climáticos, como o vento e sua intensidade, a umidade, como é o caso da neblina, a pressão atmosférica e as variações de temperatura, podem definir diferentes categorias climáticas e influir fortemente na viticultura de uma área.

            """)

  


