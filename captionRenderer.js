const content = document.getElementById('content');
const header = document.querySelector('.header');
const closeBtn = document.getElementById('closeBtn');
const settingsBtn = document.getElementById('settingsBtn');

closeBtn.addEventListener('click', (e) => {
  window.superLinguist.captionWindowClose();
})

const toCss = (v) => {
  if (v == null) return '';
  return (typeof v === 'number' || /^\d+$/.test(String(v))) ? `${v}px` : String(v);
};

window.superLinguist.onCaptionWindowDimensionsChanged((width, height) => {

  const w = toCss(width);
  const h = toCss(height);

  if (w) content.style.width = w;
  if (h) content.style.height = h;
});

window.superLinguist.onCaptionWindowContentChanged((data) => {
  window.superLinguist.print(data);
})