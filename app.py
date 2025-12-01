<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<style>
  /* デザイン調整（WordPressのテーマに合わせて調整可能） */
  .gif-converter-wrapper {
    font-family: sans-serif;
    padding: 20px;
    border: 1px solid #ddd;
    border-radius: 8px;
    background: #f9f9f9;
    max-width: 600px;
    margin: 0 auto;
  }
  .btn-convert {
    background-color: #0073aa;
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    margin-top: 10px;
  }
  .btn-convert:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }
  #status { margin-top: 10px; font-weight: bold; color: #333; }
  #output-image { max-width: 100%; margin-top: 20px; display: none; border: 1px solid #ccc; }
  .download-link { display: block; margin-top: 10px; color: #0073aa; text-decoration: underline; cursor: pointer;}
</style>
<script src="https://cdn.jsdelivr.net/npm/@ffmpeg/ffmpeg@0.11.0/dist/ffmpeg.min.js"></script>
</head>
<body>

<div class="gif-converter-wrapper">
  <h3>🎞️ 動画 to GIF 変換ツール</h3>
  <p>動画ファイル(mp4/webm等)を選択してください。ブラウザ上で処理されます。</p>
  
  <input type="file" id="uploader" accept="video/mp4, video/webm, video/mov">
  <br>
  
  <div style="margin-top:15px;">
    <label>フレームレート(FPS): <input type="number" id="fps" value="10" style="width:50px;"></label>
    <label style="margin-left:10px;">幅(px): <input type="number" id="width" value="320" style="width:60px;"></label>
  </div>

  <button id="convert-btn" class="btn-convert">GIFに変換する</button>
  
  <div id="status"></div>
  
  <img id="output-image" />
  <a id="download-link" class="download-link" style="display:none;">GIFをダウンロード</a>
</div>

<script>
  const { createFFmpeg, fetchFile } = FFmpeg;
  // 重要: 本番環境でのエラー回避のためcoreパスを指定
  const ffmpeg = createFFmpeg({ 
    log: true,
    corePath: 'https://cdn.jsdelivr.net/npm/@ffmpeg/core@0.11.0/dist/ffmpeg-core.js'
  });

  const transcode = async () => {
    const statusText = document.getElementById('status');
    const uploader = document.getElementById('uploader');
    const convertBtn = document.getElementById('convert-btn');
    const fps = document.getElementById('fps').value;
    const width = document.getElementById('width').value;

    if(uploader.files.length === 0) {
      alert("ファイルを選択してください");
      return;
    }

    const file = uploader.files[0];
    convertBtn.disabled = true;
    statusText.innerText = 'エンジンの起動中...（初回は時間がかかります）';

    if (!ffmpeg.isLoaded()) {
      await ffmpeg.load();
    }

    statusText.innerText = '変換処理中...';
    
    // ファイルをffmpegの仮想ファイルシステムに書き込み
    ffmpeg.FS('writeFile', 'input.mp4', await fetchFile(file));

    // FFmpegコマンド実行 (FPS設定、リサイズ、パレット生成による画質最適化)
    // 注意: 複雑なフィルタは処理が重くなるため、簡易的な変換を行います
    await ffmpeg.run(
        '-i', 'input.mp4', 
        '-vf', `fps=${fps},scale=${width}:-1`, 
        'output.gif'
    );

    // 生成されたデータを読み込み
    const data = ffmpeg.FS('readFile', 'output.gif');

    // Blob URLを作成して表示
    const url = URL.createObjectURL(new Blob([data.buffer], { type: 'image/gif' }));
    
    const outputImage = document.getElementById('output-image');
    outputImage.src = url;
    outputImage.style.display = 'block';
    
    const downloadLink = document.getElementById('download-link');
    downloadLink.href = url;
    downloadLink.download = 'converted.gif';
    downloadLink.style.display = 'block';

    statusText.innerText = '完了しました！';
    convertBtn.disabled = false;
  }

  document.getElementById('convert-btn').addEventListener('click', transcode);
</script>

</body>
</html>