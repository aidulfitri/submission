import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import seaborn as sns
from babel.numbers import format_currency
import plotly.express as px
sns.set(style='ticks')
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA


df = pd.read_csv("https://raw.githubusercontent.com/aidulfitri/submission/main/dashboard/main_data.csv")
df['dteday']=pd.to_datetime(df['dteday'])

min_date = df["dteday"].min()
max_date = df["dteday"].max()

# ----- SIDEBAR -----

with st.sidebar:
    # add capital bikeshare logo
    st.image("https://raw.githubusercontent.com/aidulfitri/submission/main/dashboard/LogoPNG.png")

    st.sidebar.header("Pengaturan:")

    # mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label="Atur Tanggal", min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

st.sidebar.header("Profil Saya:")
st.sidebar.markdown("Aidul Fitri Mustamin")

main_df = df[
    (df["dteday"] >= str(start_date)) &
    (df["dteday"] <= str(end_date))
]

# ----- MAINPAGE -----
st.title("WheelWise🎯 : Bike Sharing User Insights Navigator Dashboard")
css = """
<style>
.justify-text {
    text-align: justify;
    text-justify: inter-word;
}
</style>
"""

st.markdown(css, unsafe_allow_html=True)
st.markdown('<div class="justify-text">Saat ini dikenal istilah Sepeda Berbagi dimana pengguna dapat dengan mudah menyewa sepeda dari posisi tertentu dan mengembalikannya di posisi lain. Oleh karena itu, WheelWise: Bike Sharing User Insights Navigator Dashboard hadir memberikan visualisasi yang informatif dan interaktif tentang pengguna sepeda berbagi, termasuk statistik jumlah pengguna, tren penggunaan sepeda berbagi berdasarkan bulan, hari, dan musim. Dashboard ini memungkinkan pengguna untuk mengeksplorasi data dengan mudah dan mendapatkan wawasan yang lebih baik tentang pola penggunaan sepeda berbagi serta dampaknya terhadap lalu lintas, lingkungan, dan kesehatan di kota.</div>', unsafe_allow_html=True)
st.markdown('##')

# Menghitung total semua pengendara
total_all_rides = main_df['cnt'].sum()

# Menghitung total pengendara yang terdaftar
total_register_rides = main_df['registered'].sum()

# Menghitung total pengendara yang tidak terdaftar
total_casual_rides = main_df['casual'].sum()

with st.container():
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Pengendara", value=total_all_rides)

    with col2:
        st.metric("Jumlah Pengendara Terdaftar", value=total_register_rides)

    with col3:
        st.metric("Jumlah Pengendara Tidak Terdaftar", value=total_casual_rides)


st.markdown("---")

#Data

def buat_pengguna_bulanan_df(df):
    pengguna_bulanan_df = df.resample(rule='M', on='dteday').agg({
        "casual": "sum",
        "registered": "sum",
        "cnt": "sum"  # Ganti count_rides menjadi cnt
    })
    pengguna_bulanan_df.index = pengguna_bulanan_df.index.strftime('%b-%y')
    pengguna_bulanan_df = pengguna_bulanan_df.reset_index().rename(columns={
        "dteday": "Bulan-Tahun",
        "cnt": "Jumlah Pengendara",  # Ganti count_rides menjadi cnt
        "casual": "Pengendara Tidak Teregistrasi",
        "registered": "Pengendara Teregistrasi"
    })
    
    return pengguna_bulanan_df

def buat_pengendara_musim_df(df):
    pengendara_musim_df = df.groupby("season").agg({
        "casual": "sum",
        "registered": "sum",
        "cnt": "sum"
    })
    pengendara_musim_df = pengendara_musim_df.reset_index()
    pengendara_musim_df.rename(columns={
        "cnt": "Jumlah Pengendara",
        "casual": "Pengendara Tidak Teregistrasi",
        "registered": "Pengendara Teregistrasi"
    }, inplace=True)
    
    pengendara_musim_df = pd.melt(pengendara_musim_df,
                                  id_vars=['season'],
                                  value_vars=['Pengendara Tidak Teregistrasi', 'Pengendara Teregistrasi'],
                                  var_name='type_of_rides',
                                  value_name='count_rides')
    
    pengendara_musim_df['season'] = pd.Categorical(pengendara_musim_df['season'],
                                             categories=['Spring', 'Summer', 'Fall', 'Winter'])
    
    pengendara_musim_df = pengendara_musim_df.sort_values('season')
    
    return pengendara_musim_df

min_date = df["dteday"].min()
max_date = df["dteday"].max()

main_df = df[
    (df["dteday"] >= str(start_date)) &
    (df["dteday"] <= str(end_date))
]

pengguna_bulanan_df = buat_pengguna_bulanan_df(main_df)
pengendara_musim_df = buat_pengendara_musim_df(main_df)
# ----- CHART -----
fig = px.line(pengguna_bulanan_df,
              x='Bulan-Tahun',
              y=['Pengendara Tidak Teregistrasi', 'Pengendara Teregistrasi', 'Jumlah Pengendara'],
              color_discrete_sequence=["blue", "darkseagreen", "lightblue"],
              markers=True,
              title="Jumlah Pengendara Sepeda Berbagi").update_layout(xaxis_title='', yaxis_title='Jumlah Pengendara')

st.plotly_chart(fig, use_container_width=True)

fig = px.bar(pengendara_musim_df,
              x='season',
              y='count_rides',
              color='type_of_rides',
              barmode='group',
              color_discrete_sequence=["lightblue", "darkseagreen"],
              title='Jumlah Pengendara Sepeda Berbagi berdasarkan Musim').update_layout(xaxis_title='', yaxis_title='Jumlah Pengendara')


st.plotly_chart(fig, use_container_width=True)

#ANALISIS RUNTUN WAKTU
st.title("Analisis Runtun Waktu")
forecast_year = st.number_input("Masukkan tahun yang ingin Anda ramal:", min_value=int(min_date.year), max_value=int(2100))
main_df['dteday'] = pd.to_datetime(main_df['dteday'])
main_df.set_index('dteday', inplace=True)

forecast_data = main_df[main_df.index.year <= forecast_year]
model = ARIMA(forecast_data['cnt'], order=(1, 1, 1))
results = model.fit()
forecast_steps = 12
forecast = results.get_forecast(steps=forecast_steps)

# ----- DIAGRAM GARIS UNTUK RAMALAN -----
forecast_index = pd.date_range(forecast_data.index[-1], periods=forecast_steps + 1, freq='M')[1:]
forecast_df = pd.DataFrame({'Ramalan': forecast.predicted_mean.values}, index=forecast_index)
fig_forecast = px.line(forecast_df, x=forecast_df.index, y='Ramalan', labels={'y': 'Jumlah Ramalan'}, title=f'Analisis Runtun Waktu untuk Jumlah Pengendara Sepeda Berbagi Pada Tahun {forecast_year} Adalah')

st.plotly_chart(fig_forecast, use_container_width=True)
