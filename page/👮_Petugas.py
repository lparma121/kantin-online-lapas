# --- PERBAIKAN AREA PETUGAS ---
elif menu == "👮 Area Petugas":
    if not authenticated:
        st.warning("Masukkan password di sidebar.")
    else:
        st.title("Panel Petugas")
        res_p = supabase.table("pesanan").select("*").neq("status", "Selesai").execute()
        
        if res_p.data:
            for p in res_p.data:
                # Gunakan form agar aplikasi tidak refresh otomatis saat ambil foto
                with st.expander(f"Order #{p['id']} - {p['untuk_siapa']}"):
                    with st.form(key=f"form_{p['id']}"):
                        st_baru = st.selectbox("Update Status", ["Menunggu Antrian", "Diproses", "Selesai"])
                        
                        # Kamera diletakkan di dalam form
                        foto = st.camera_input("Ambil Foto Penyerahan")
                        
                        submit_petugas = st.form_submit_button("Simpan & Kirim Notifikasi")
                        
                        if submit_petugas:
                            u_data = {"status": st_baru}
                            
                            # Cek apakah foto berhasil diambil
                            if st_baru == "Selesai" and foto is not None:
                                path = f"bukti_{p['id']}.png"
                                # Proses unggah ke storage
                                supabase.storage.from_("kantin-assets").upload(path, foto.getvalue(), {"upsert": "true"})
                                u_data["foto_penerima"] = supabase.storage.from_("kantin-assets").get_public_url(path)
                                
                                # Simpan perubahan ke database
                                supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                                
                                # Siapkan Link WA
                                pesan_wa = f"Halo {p['nama_pemesan']}, pesanan #{p['id']} untuk {p['untuk_siapa']} TELAH DITERIMA petugas. Terima kasih."
                                no_hp = p['nomor_wa']
                                if no_hp.startswith('0'): no_hp = '62' + no_hp[1:]
                                wa_url = f"https://wa.me/{no_hp}?text={pesan_wa.replace(' ', '%20')}"
                                
                                st.success("Data & Foto Berhasil Tersimpan!")
                                st.link_button("📲 Kirim WhatsApp Sekarang", wa_url)
                            elif st_baru == "Selesai" and foto is None:
                                st.error("Foto wajib diambil jika status Selesai!")
                            else:
                                # Update status biasa tanpa foto
                                supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                                st.rerun()
        else:
            st.info("Belum ada antrian pesanan.")
