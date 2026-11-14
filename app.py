import cv2
import numpy as np
import streamlit as st
import tempfile
import os
import av
from datetime import datetime
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase

from src.filters import apply_filter

# إعدادات الصفحة
st.set_page_config(page_title="Image to Art Advanced", page_icon="🎨", layout="wide")

# تهيئة الذاكرة للسجل
if 'history' not in st.session_state:
    st.session_state.history = []

st.title("🎨 Image to Art Converter - Advanced")
st.write("تطبيق متكامل لتحويل الصور والفيديو باستخدام OpenCV و Streamlit.")

# إنشاء التبويبات الثلاثة
tab_image, tab_video, tab_history = st.tabs(["🖼️ تحويل الصور", "🎬 الفيديو والكاميرا", "📜 سجل العمليات"])

# ==========================================
# التبويب الأول: الصور
# ==========================================
with tab_image:
    st.header("تحويل صورة إلى فن")

    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("⚙️ الإعدادات")
        filter_name = st.selectbox(
            "اختر الفلتر",
            options=["sketch", "color_sketch", "cartoon", "background"],
            format_func=lambda x: {
                "sketch": "رسم بالقلم الرصاص",
                "color_sketch": "رسم ملوّن",
                "cartoon": "تأثير كرتوني",
                "background": "تلوين الخلفية",
            }[x],
            key="img_filter"
        )

        sketch_detail = 21
        blur_val = 9
        edge_val = 9

        if filter_name in ["sketch", "color_sketch"]:
            sketch_detail = st.slider("درجة وضوح الرسم الرصاصي", min_value=5, max_value=51, value=21, step=2)
        elif filter_name == "cartoon":
            blur_val = st.slider("نعومة الألوان (Blur)", min_value=3, max_value=31, value=9, step=2)
            edge_val = st.slider("حدة الحواف (Edges)", min_value=3, max_value=31, value=9, step=2)

    with col2:
        uploaded = st.file_uploader("ارفع صورة (JPG, PNG)", type=["jpg", "jpeg", "png"])

        if uploaded is not None:
            file_bytes = np.asarray(bytearray(uploaded.read()), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            col_before, col_after = st.columns(2)
            with col_before:
                st.subheader("قبل")
                st.image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), use_column_width=True)

            with col_after:
                st.subheader("بعد")
                result = apply_filter(image, filter_name, blur_val, edge_val, sketch_detail)
                st.image(cv2.cvtColor(result, cv2.COLOR_BGR2RGB), use_column_width=True)

                _, buffer = cv2.imencode(".png", result)
                st.download_button(
                    "⬇️ تحميل النتيجة",
                    data=buffer.tobytes(),
                    file_name=f"result_{filter_name}.png",
                    mime="image/png",
                )

                if st.button("💾 حفظ في السجل"):
                    st.session_state.history.append({
                        "الوقت": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "الفلتر": filter_name,
                        "النوع": "صورة"
                    })
                    st.success("تمت الإضافة إلى السجل!")

# ==========================================
# التبويب الثاني: الفيديو والكاميرا
# ==========================================
with tab_video:
    st.header("معالجة الفيديو والكاميرا")

    # تقسيم التبويب إلى قسمين (الكاميرا المباشرة | رفع الفيديو)
    live_tab, upload_tab = st.tabs(["🔴 الكاميرا المباشرة (Live)", "📁 رفع فيديو مسجل"])

    # --- القسم الأول: الكاميرا المباشرة ---
    with live_tab:
        st.info("اضغط على زر START أدناه، واسمح للمتصفح بالوصول إلى الكاميرا. يمكنك تغيير الفلتر أثناء البث.")

        live_filter = st.selectbox(
            "اختر فلتر الكاميرا",
            options=["sketch", "color_sketch", "cartoon", "background"],
            format_func=lambda x:
            {"sketch": "رسم رصاص", "color_sketch": "رسم ملوّن", "cartoon": "كرتون", "background": "عزل الخلفية"}[x],
            key="live_filter_select"
        )


        class VideoProcessor(VideoProcessorBase):
            def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
                img = frame.to_ndarray(format="bgr24")
                processed_img = apply_filter(img, live_filter)
                return av.VideoFrame.from_ndarray(processed_img, format="bgr24")


        webrtc_streamer(
            key="image-to-art-live",
            video_processor_factory=VideoProcessor,
            media_stream_constraints={"video": True, "audio": False},
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        )

    # --- القسم الثاني: رفع فيديو مسجل ---
    with upload_tab:
        video_file = st.file_uploader("ارفع فيديو (MP4, AVI)", type=["mp4", "avi", "mov"])

        if video_file is not None:
            # حفظ الفيديو مؤقتاً
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            tfile.write(video_file.read())

            st.video(tfile.name)
            st.warning("معالجة الفيديو بالكامل تأخذ وقتاً، اضغط الزر أدناه لمعالجة أول 5 ثوانٍ فقط.")

            if st.button("▶️ تطبيق الفلتر على أول 5 ثوانٍ"):
                cap = cv2.VideoCapture(tfile.name)
                fps = cap.get(cv2.CAP_PROP_FPS)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                out_path = "output_video.mp4"
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

                frames_to_process = int(fps * 5)
                progress_bar = st.progress(0)

                for i in range(frames_to_process):
                    ret, frame = cap.read()
                    if not ret:
                        break
                    processed_frame = apply_filter(frame, "sketch")
                    out.write(processed_frame)
                    progress_bar.progress((i + 1) / frames_to_process)

                cap.release()
                out.release()

                st.success("✅ تمت المعالجة بنجاح!")
                st.video(out_path)

                st.session_state.history.append({
                    "الوقت": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "الفلتر": "sketch",
                    "النوع": "فيديو"
                })

                # تجاهل خطأ حذف الملف المؤقت في ويندوز
                try:
                    os.remove(tfile.name)
                except PermissionError:
                    pass

# ==========================================
# التبويب الثالث: السجل
# ==========================================
with tab_history:
    st.header("📜 سجل العمليات")
    if len(st.session_state.history) == 0:
        st.write("لا توجد عمليات مسجلة بعد. قم بتحويل صورة أو فيديو واحفظه في السجل.")
    else:
        st.table(st.session_state.history)
        if st.button("🗑️ مسح السجل"):
            st.session_state.history = []
            st.rerun()