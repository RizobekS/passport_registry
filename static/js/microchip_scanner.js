document.addEventListener("DOMContentLoaded", function () {
  const input = document.querySelector("#id_microchip");
  if (!input) return;

  const btn = document.createElement("button");
  btn.type = "button";
  btn.innerText = "📷 Scan";
  btn.style.marginRight = "10px";

  input.parentNode.insertBefore(btn, input);

  const readerDiv = document.createElement("div");
  readerDiv.id = "reader";
  readerDiv.style.width = "320px";
  readerDiv.style.display = "none";
  readerDiv.style.marginTop = "8px";
  input.parentNode.appendChild(readerDiv);

  let html5QrCode = null;

  async function chooseRearCamera() {
    try {
      const cameras = await Html5Qrcode.getCameras();
      if (!cameras || cameras.length === 0) return null;

      const rearKeywords = ["back", "rear", "environment", "back camera"];
      const found = cameras.find(cam =>
        cam.label && rearKeywords.some(k => cam.label.toLowerCase().includes(k))
      );
      if (found) return found.id;

      return cameras[cameras.length - 1].id;
    } catch (err) {
      console.warn("chooseRearCamera error:", err);
      return null;
    }
  }

  async function startScannerWithRear() {
    if (html5QrCode) {
      try { await html5QrCode.stop(); } catch (e) {}
      html5QrCode = null;
    }

    readerDiv.style.display = "block";
    btn.innerText = "⏹ Stop";

    html5QrCode = new Html5Qrcode("reader");
    const config = { fps: 10, qrbox: { width: 250, height: 250 } };

    let deviceConstraint = null;
    const rearId = await chooseRearCamera();
    if (rearId) {
      deviceConstraint = { deviceId: { exact: rearId } };
    } else {
      deviceConstraint = { facingMode: { ideal: "environment" } };
    }

    try {
      await html5QrCode.start(
        deviceConstraint,
        config,
        (decodedText) => {
          input.value = decodedText;
          input.dispatchEvent(new Event('input', { bubbles: true }));
          input.dispatchEvent(new Event('change', { bubbles: true }));

          html5QrCode.stop().then(() => {
            readerDiv.style.display = "none";
            btn.innerText = "📷 Scan";
            html5QrCode = null;
          });
        },
        (errorMessage) => console.debug("scan error:", errorMessage)
      );
    } catch (err) {
      console.error("Scanner start error:", err);
      alert("Kamerani ishga tushirishda xato. Iltimos, HTTPS va brauzer ruxsatlarini tekshiring.");
      readerDiv.style.display = "none";
      btn.innerText = "📷 Scan";
      html5QrCode = null;
    }
  }

  btn.addEventListener("click", async function () {
    if (readerDiv.style.display === "block") {
      if (html5QrCode) { try { await html5QrCode.stop(); } catch (e) {} }
      readerDiv.style.display = "none";
      btn.innerText = "📷 Scan";
      html5QrCode = null;
      return;
    }
    await startScannerWithRear();
  });

});
