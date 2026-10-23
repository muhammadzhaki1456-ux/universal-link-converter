const form = document.querySelector("#convert-form");
const input = document.querySelector("#url");
const submit = document.querySelector("#submit");
const result = document.querySelector("#result");
const title = document.querySelector("#result-title");
const message = document.querySelector("#message");
const urlRow = document.querySelector("#url-row");
const mediafireUrl = document.querySelector("#mediafire-url");
const copyButton = document.querySelector("#copy");
const finalUrl = document.querySelector("#final-url");
let urlToCopy = "";

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  result.hidden = false;
  urlRow.hidden = true;
  finalUrl.hidden = true;
  title.textContent = "Sedang memeriksa…";
  message.textContent = "Mohon tunggu sebentar.";
  submit.disabled = true;
  submit.textContent = "Memeriksa…";
  try {
    const response = await fetch("/api/convert", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({url: input.value.trim()})
    });
    const data = await response.json();
    title.textContent = data.found ? "Link MediaFire ditemukan" : "Hasil pemeriksaan";
    message.textContent = data.message || "Tidak ada hasil.";
    if (data.found && data.mediafire_url) {
      urlToCopy = data.mediafire_url;
      mediafireUrl.href = data.mediafire_url;
      mediafireUrl.textContent = data.mediafire_url;
      urlRow.hidden = false;
    }
    if (data.final_url) {
      finalUrl.textContent = "URL yang diperiksa: " + data.final_url;
      finalUrl.hidden = false;
    }
  } catch (_) {
    title.textContent = "Pemeriksaan gagal";
    message.textContent = "Tidak dapat terhubung ke server. Coba lagi nanti.";
  } finally {
    submit.disabled = false;
    submit.innerHTML = 'Periksa Link <span aria-hidden="true">→</span>';
  }
});

copyButton.addEventListener("click", async () => {
  if (!urlToCopy) return;
  try {
    await navigator.clipboard.writeText(urlToCopy);
    copyButton.textContent = "Tersalin!";
    setTimeout(() => { copyButton.textContent = "Salin URL"; }, 1500);
  } catch (_) {
    copyButton.textContent = "Gagal menyalin";
  }
});
