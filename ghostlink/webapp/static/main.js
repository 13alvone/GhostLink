const UI = (() => {
  let overlay;
  function init() {
    overlay = document.getElementById('loading-overlay');
  }
  function showOverlay() {
    overlay.style.display = 'flex';
  }
  function hideOverlay() {
    overlay.style.display = 'none';
  }
  function setDisabled(form, disabled) {
    form.querySelectorAll('input, textarea, button, select').forEach(el => {
      el.disabled = disabled;
    });
  }
  return { init, showOverlay, hideOverlay, setDisabled };
})();

const Encoder = (() => {
  let form, textInput, fileInput, error;
  async function handleSubmit(e) {
    const text = textInput.value.trim();
    const file = fileInput.files[0];
    error.textContent = '';

    if (text && file) {
      e.preventDefault();
      error.textContent = 'Provide either text or file, not both.';
      return;
    }
    if (!text && !file) {
      e.preventDefault();
      error.textContent = 'Provide text or file.';
      return;
    }

    e.preventDefault();
    const formData = new FormData(form);
    if (file) {
      formData.delete('text');
    } else {
      formData.delete('file');
    }

    UI.showOverlay();
    UI.setDisabled(form, true);
    try {
      const response = await fetch('/encode', { method: 'POST', body: formData });
      if (!response.ok) {
        const data = await response.json().catch(() => ({ detail: 'Server error' }));
        error.textContent = data.detail || 'Server error';
        return;
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const disposition = response.headers.get('Content-Disposition');
      let filename = 'output.wav';
      if (disposition) {
        const match = disposition.match(/filename="?([^";]+)"?/);
        if (match) filename = match[1];
      }
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      error.textContent = 'Network error';
    } finally {
      UI.hideOverlay();
      UI.setDisabled(form, false);
    }
  }

  function init() {
    form = document.getElementById('encode-form');
    textInput = document.getElementById('text-input');
    fileInput = document.getElementById('file-input');
    error = document.getElementById('encode-error');
    form.addEventListener('submit', handleSubmit);
  }
  return { init };
})();

const Decoder = (() => {
  let form, error, output, wavInput, copyBtn;
  async function handleSubmit(e) {
    e.preventDefault();
    error.textContent = '';
    output.value = '';
    const file = wavInput.files[0];
    if (!file) {
      error.textContent = 'Provide a WAV file.';
      return;
    }
    const formData = new FormData(form);

    UI.showOverlay();
    UI.setDisabled(form, true);
    try {
      const response = await fetch('/decode', { method: 'POST', body: formData });
      if (!response.ok) {
        const data = await response.json().catch(() => ({ detail: 'Server error' }));
        error.textContent = data.detail || 'Server error';
        return;
      }
      const text = await response.text();
      output.value = text;
    } catch (err) {
      error.textContent = 'Network error';
    } finally {
      UI.hideOverlay();
      UI.setDisabled(form, false);
    }
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(output.value);
    } catch {
      error.textContent = 'Copy failed';
    }
  }

  function init() {
    form = document.getElementById('decode-form');
    error = document.getElementById('decode-error');
    output = document.getElementById('decode-output');
    wavInput = document.getElementById('wav-input');
    copyBtn = document.getElementById('copy-btn');
    form.addEventListener('submit', handleSubmit);
    copyBtn.addEventListener('click', copy);
  }
  return { init };
})();

export { UI, Encoder, Decoder };

document.addEventListener('DOMContentLoaded', () => {
  UI.init();
  Encoder.init();
  Decoder.init();
});

