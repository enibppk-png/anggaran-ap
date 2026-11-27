import streamlit as st
import pandas as pd
import pickle
import altair as alt
import Orange

st.title("Dashboard Analitik DJPb")

# Sidebar Filter
st.sidebar.header("Menu Filter")
opsi = st.sidebar.selectbox("Pilih Model:", ["Klasifikasi", "Regresi"])

data = pd.read_csv("data/02_realisasi_anggaran_klasifikasi.csv")


@st.cache_resource
def load_model():
    with open("models/Best_model.pkcls", "rb") as model_file:
        return pickle.load(model_file)


model = load_model()

tab_prediksi, tab_visualisasi = st.tabs(["Menu Prediksi", "Visualisasi"])

with tab_prediksi:
    st.header("Prediksi Realisasi 95%")
    st.markdown("Masukkan data input berikut.")

    col1, col2 = st.columns(2)
    with col1:
        jumlah_spm = st.number_input(
            "Jumlah SPM",
            min_value=1,
            max_value=200,
            value=10,
            step=1,
            format="%d",
        )
        revisi_dipa = st.number_input(
            "Revisi DIPA",
            min_value=0,
            max_value=5,
            value=1,
            step=1,
            format="%d",
        )
        deviasi_rpd_persen = st.number_input(
            "Deviasi RPD (%)",
            min_value=0.00,
            max_value=30.00,
            value=5.50,
            format="%.2f",
        )
    with col2:
        skor_ikpa = st.slider(
            "Skor IKPA",
            min_value=70.00,
            max_value=100.00,
            value=85.00,
            step=0.1,
            format="%.2f",
        )
        tipe_satker = st.selectbox(
            "Tipe Satker",
            [
                "Dekonsentrasi",
                "Kantor Daerah",
                "Kantor Pusat",
                "Tugas Pembantuan",
            ],
        )
    if st.button("Prediksi", type="primary"):
        if model is None:
            st.error("Model belum tersedia.")
        else:
            tipe_values = [
                "Dekonsentrasi",
                "Kantor Daerah",
                "Kantor Pusat",
                "Tugas Pembantuan",
            ]
            tipe_indicators = [
                1.0 if tipe_satker == tipe_value else 0.0
                for tipe_value in tipe_values
            ]
            input_row = [
                float(jumlah_spm),
                float(revisi_dipa),
                float(deviasi_rpd_persen),
                float(skor_ikpa),
                *tipe_indicators,
            ]

            try:
                table = Orange.data.Table.from_list(model.domain, [input_row])
                prediction_index = int(model(table)[0])
                probabilities = model(table, model.Probs)[0]
                class_name = model.domain.class_var.values[prediction_index]
                confidence = float(probabilities[prediction_index])

                if class_name == "Ya":
                    st.success(f"Prediksi: {class_name} (keyakinan {confidence:.1%})")
                else:
                    st.warning(f"Prediksi: {class_name} (keyakinan {confidence:.1%})")
            except Exception as exc:
                st.error(f"Prediksi gagal dijalankan: {exc}")


with tab_visualisasi:
    garis_ikpa = (
        alt.Chart(pd.DataFrame({"skor_ikpa": [skor_ikpa]}))
        .mark_rule(color="#d62728", strokeDash=[6, 4], strokeWidth=2)
        .encode(
            x=alt.X(
                "skor_ikpa:Q",
                title="Skor IKPA",
                scale=alt.Scale(domain=[70, 100]),
            ),
            tooltip=alt.Tooltip("skor_ikpa:Q", title="Skor IKPA pilihan"),
        )
    )
    st.caption(
        f"Garis putus-putus menandai Skor IKPA pilihan: {skor_ikpa:.2f}."
    )

    st.header("Visualisasi Bubble Plot")
    st.markdown(
        "Grafik bubble menunjukkan skor IKPA terhadap deviasi RPD, dengan warna berdasarkan kolom `realisasi_tercapai_95persen`."
    )

    bubble_plot = (
        alt.Chart(data)
        .mark_circle(opacity=0.7, size=100)
        .encode(
            x=alt.X(
                "skor_ikpa",
                title="Skor IKPA",
                scale=alt.Scale(domain=[70, 100]),
            ),
            y=alt.Y("deviasi_rpd_persen", title="Deviasi RPD (%)"),
            color=alt.Color(
                "realisasi_tercapai_95persen:N",
                title="Realisasi Tercapai 95%",
                scale=alt.Scale(
                    domain=["Tidak", "Ya"],
                    range=["#d62728", "#2ca02c"],
                ),
            ),
            tooltip=[
                "kode_satker",
                "tipe_satker",
                "skor_ikpa",
                "deviasi_rpd_persen",
                "realisasi_tercapai_95persen",
            ],
        )
    )
    chart = (
        alt.layer(bubble_plot, garis_ikpa)
        .properties(width=900, height=550)
        .interactive()
    )
    st.altair_chart(chart, width=900)

    st.header("Histogram Seluruh Skor IKPA")
    st.markdown(
        "Distribusi Skor IKPA untuk seluruh satuan kerja dalam data."
    )

    histogram_bars = (
        alt.Chart(data)
        .mark_bar(color="#4c78a8")
        .encode(
            x=alt.X(
                "skor_ikpa",
                title="Skor IKPA",
                bin=alt.Bin(maxbins=20),
            ),
            y=alt.Y(
                "count():Q",
                title="Jumlah Satuan Kerja",
            ),
            tooltip=[
                alt.Tooltip("count():Q", title="Jumlah Satuan Kerja"),
            ],
        )
    )
    histogram = (
        alt.layer(histogram_bars, garis_ikpa)
        .properties(width=900, height=550)
        .interactive()
    )
    st.altair_chart(histogram, width=900)

    st.header("Sebaran Skor IKPA pada Peta")
    st.markdown(
        "Ukuran dan warna lingkaran menunjukkan rata-rata Skor IKPA per provinsi."
    )

    koordinat_provinsi = {
        "Aceh": (-5.55, 95.32),
        "Bali": (-8.65, 115.22),
        "DKI Jakarta": (-6.18, 106.83),
        "Jawa Barat": (-6.92, 107.60),
        "Jawa Tengah": (-7.15, 110.14),
        "Jawa Timur": (-7.25, 112.24),
        "Kalimantan Timur": (-1.27, 116.83),
        "Lampung": (-5.45, 105.25),
        "NTB": (-8.58, 116.10),
        "NTT": (-9.60, 123.77),
        "Papua": (-4.27, 138.96),
        "Riau": (0.51, 101.45),
        "Sulawesi Selatan": (-3.58, 119.97),
        "Sumatera Barat": (-0.95, 100.35),
        "Sumatera Utara": (2.01, 99.66),
    }

    sebaran_ikpa = (
        data.groupby("provinsi", as_index=False)
        .agg(
            rata_rata_ikpa=("skor_ikpa", "mean"),
            jumlah_satker=("skor_ikpa", "count"),
        )
        .dropna(subset=["rata_rata_ikpa"])
    )
    sebaran_ikpa["lat"] = sebaran_ikpa["provinsi"].map(
        lambda provinsi: koordinat_provinsi.get(provinsi, (None, None))[0]
    )
    sebaran_ikpa["lon"] = sebaran_ikpa["provinsi"].map(
        lambda provinsi: koordinat_provinsi.get(provinsi, (None, None))[1]
    )
    sebaran_ikpa = sebaran_ikpa.dropna(subset=["lat", "lon"])
    sebaran_ikpa["rata_rata_ikpa"] = sebaran_ikpa["rata_rata_ikpa"].round(2)
    sebaran_ikpa["warna"] = sebaran_ikpa["rata_rata_ikpa"].apply(
        lambda skor: [46, 160, 67]
        if skor >= 90
        else [255, 191, 0]
        if skor >= 80
        else [214, 39, 40]
    )

    st.map(
        sebaran_ikpa,
        latitude="lat",
        longitude="lon",
        size="rata_rata_ikpa",
        color="warna",
        zoom=4,
    )

    st.dataframe(
        sebaran_ikpa[
            ["provinsi", "rata_rata_ikpa", "jumlah_satker"]
        ].rename(
            columns={
                "provinsi": "Provinsi",
                "rata_rata_ikpa": "Rata-rata IKPA",
                "jumlah_satker": "Jumlah Satuan Kerja",
            }
        ),
        width="stretch",
        hide_index=True,
    )

    st.header("Ranking Satuan Kerja Berdasarkan Skor IKPA")

    kolom_ranking = [
        "kode_satker",
        "nama_kementerian",
        "provinsi",
        "tipe_satker",
        "skor_ikpa",
    ]

    ranking_tertinggi = (
        data[kolom_ranking]
        .sort_values("skor_ikpa", ascending=False)
        .head(10)
        .rename(
            columns={
                "kode_satker": "Kode Satker",
                "nama_kementerian": "Kementerian",
                "provinsi": "Provinsi",
                "tipe_satker": "Tipe Satker",
                "skor_ikpa": "Skor IKPA",
            }
        )
    )

    ranking_terendah = (
        data[kolom_ranking]
        .sort_values("skor_ikpa", ascending=True)
        .head(5)
        .rename(
            columns={
                "kode_satker": "Kode Satker",
                "nama_kementerian": "Kementerian",
                "provinsi": "Provinsi",
                "tipe_satker": "Tipe Satker",
                "skor_ikpa": "Skor IKPA",
            }
        )
    )

    kolom_kiri, kolom_kanan = st.columns(2)

    with kolom_kiri:
        st.subheader("10 Satker dengan IKPA Tertinggi")
        st.dataframe(ranking_tertinggi, width="stretch", hide_index=True)

    with kolom_kanan:
        st.subheader("5 Satker dengan IKPA Terendah")
        st.dataframe(ranking_terendah, width="stretch", hide_index=True)

    st.header("Satker dengan Revisi DIPA Terbanyak")
    st.markdown("Peringkat berdasarkan jumlah revisi DIPA pada data.")

    ranking_revisi = (
        data[
            [
                "kode_satker",
                "nama_kementerian",
                "provinsi",
                "revisi_dipa",
            ]
        ]
        .sort_values("revisi_dipa", ascending=False)
        .head(10)
        .rename(
            columns={
                "kode_satker": "Kode Satker",
                "nama_kementerian": "Kementerian",
                "provinsi": "Provinsi",
                "revisi_dipa": "Jumlah Revisi DIPA",
            }
        )
    )
    st.dataframe(ranking_revisi, width="stretch", hide_index=True)

    st.header("5 Satker dengan Penyerapan Terbaik")
    st.markdown("Peringkat berdasarkan realisasi anggaran sampai dengan TW III.")

    ranking_penyerapan = (
        data[
            [
                "kode_satker",
                "nama_kementerian",
                "provinsi",
                "realisasi_tw3_persen",
            ]
        ]
        .sort_values("realisasi_tw3_persen", ascending=False)
        .head(5)
        .rename(
            columns={
                "kode_satker": "Kode Satker",
                "nama_kementerian": "Kementerian",
                "provinsi": "Provinsi",
                "realisasi_tw3_persen": "Penyerapan sampai TW III (%)",
            }
        )
    )
    st.dataframe(ranking_penyerapan, width="stretch", hide_index=True)

    st.header("5 Satker dengan Penyerapan Terendah")

    ranking_penyerapan_terendah = (
        data[
            [
                "kode_satker",
                "nama_kementerian",
                "provinsi",
                "realisasi_tw3_persen",
            ]
        ]
        .sort_values("realisasi_tw3_persen", ascending=True)
        .head(5)
        .rename(
            columns={
                "kode_satker": "Kode Satker",
                "nama_kementerian": "Kementerian",
                "provinsi": "Provinsi",
                "realisasi_tw3_persen": "Penyerapan sampai TW III (%)",
            }
        )
    )
    st.dataframe(ranking_penyerapan_terendah, width="stretch", hide_index=True)

    st.header("Kementerian dengan Penyerapan Terendah")
    st.markdown(
        "Penyerapan TW III dihitung secara tertimbang berdasarkan pagu satker."
    )

    ringkasan_kementerian = (
        data.assign(
            realisasi_tertimbang=lambda df: (
                df["pagu_miliar"] * df["realisasi_tw3_persen"]
            )
        )
        .groupby("nama_kementerian", as_index=False)
        .agg(
            total_pagu=("pagu_miliar", "sum"),
            total_realisasi_tertimbang=("realisasi_tertimbang", "sum"),
        )
    )
    ringkasan_kementerian["penyerapan_tw3_persen"] = (
        ringkasan_kementerian["total_realisasi_tertimbang"]
        / ringkasan_kementerian["total_pagu"]
    )

    pemetaan_menteri = {"Kemenag": "Nasaruddin Umar"}
    kementerian_terendah = (
        ringkasan_kementerian.sort_values("penyerapan_tw3_persen")
        .head(1)
        .rename(
            columns={
                "nama_kementerian": "Kementerian",
                "penyerapan_tw3_persen": "Penyerapan sampai TW III (%)",
            }
        )
    )
    kementerian_terendah["Nama Menteri"] = kementerian_terendah[
        "Kementerian"
    ].map(pemetaan_menteri)

    if kementerian_terendah["Nama Menteri"].isna().any():
        st.warning(
            "Nama menteri untuk kementerian dengan penyerapan terendah "
            "belum tersedia dalam pemetaan."
        )
        kementerian_terendah["Nama Menteri"] = kementerian_terendah[
            "Nama Menteri"
        ].fillna("Belum dipetakan")

    st.dataframe(
        kementerian_terendah[
            ["Kementerian", "Nama Menteri", "Penyerapan sampai TW III (%)"]
        ].round({"Penyerapan sampai TW III (%)": 2}),
        width="stretch",
        hide_index=True,
    )