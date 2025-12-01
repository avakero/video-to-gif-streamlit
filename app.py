import streamlit as st
import tempfile
import os
from moviepy.editor import VideoFileClip

# ページ設定
st.set_page_config(page_title="動画 to GIF コンバーター", page_icon="🎞️")

st.title("🎞️ 動画 GIF 変換アプリ")
st.write("動画ファイルをアップロードして、GIFアニメーションに変換します。")

# サイドバーで設定
st.sidebar.header("変換設定")
resize_factor = st.sidebar.slider("サイズ縮小率 (1.0 = そのまま)", 0.1, 1.0, 0.5, 0.1)
fps_value = st.sidebar.slider("フレームレート (FPS)", 5, 30, 10)
speed_factor = st.sidebar.slider("再生速度 (倍速)", 0.5, 3.0, 1.0, 0.1)

# ファイルアップロード
uploaded_file = st.file_uploader("動画ファイルを選択 (mp4, mov, avi)", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    # 一時ファイルとして保存
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_file.read())
    
    # 動画の読み込み
    clip = VideoFileClip(tfile.name)
    
    # 動画情報の表示
    st.video(uploaded_file)
    st.info(f"元の動画の長さ: {clip.duration}秒, 解像度: {clip.size}")

    # 変換ボタン
    if st.button("GIFに変換する"):
        with st.spinner('変換中...しばらくお待ちください'):
            try:
                # 設定の適用（リサイズ、速度変更）
                processed_clip = clip.resize(resize_factor).speedx(speed_factor)
                
                # 一時ファイルへGIFを出力
                gif_path = tempfile.mktemp(suffix=".gif")
                # moviepyのバージョンによってはprogram='ffmpeg'が必要
                processed_clip.write_gif(gif_path, fps=fps_value)

                # 結果の表示
                st.success("変換完了！")
                st.image(gif_path, caption="生成されたGIF")

                # ダウンロードボタン
                with open(gif_path, "rb") as file:
                    btn = st.download_button(
                        label="GIFをダウンロード",
                        data=file,
                        file_name="converted_video.gif",
                        mime="image/gif"
                    )
                
                # クリーンアップ
                try:
                    os.remove(gif_path)
                except:
                    pass

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
            
            finally:
                # 元動画の一時ファイルを閉じて削除
                clip.close()
                tfile.close()
                os.unlink(tfile.name)
