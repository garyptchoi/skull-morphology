const methods = {
  size: {image:'size.png', alt:'Geospiza difficilis skull inside its axis-aligned bounding box.', text:'Length x, width y and height z, in mm. The interpretation depends on the input mesh’s anatomical orientation.'},
  orbit: {image:'orbit.png', alt:'Geospiza difficilis skull with a fitted orbital sphere and selected inlier points.', text:'Orbit radius r, in mm; curvature is 1/r, in mm⁻¹. Check that the retained points lie on the orbital surface.'},
  braincase: {image:'braincase.png', alt:'Geospiza difficilis skull with a fitted axis-aligned braincase ellipsoid.', text:'Neurocranial semi-axes a, b and c, in mm. These are half-axis lengths of a geometric fit, not direct brain measurements.'}
};
document.querySelectorAll('[data-method]').forEach(button => button.addEventListener('click', () => {
  const method = methods[button.dataset.method];
  document.querySelectorAll('[data-method]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  const image = document.getElementById('method-image');
  image.src = 'assets/' + method.image;
  image.alt = method.alt;
  document.getElementById('method-caption').textContent = method.text;
}));
const commands = {
  mac: 'python3 -m venv .venv\nsource .venv/bin/activate\npython -m pip install -r requirements-quickstart.txt\npython quickstart.py',
  windows: 'py -3.12 -m venv .venv\n.venv\\Scripts\\activate.bat\npython -m pip install -r requirements-quickstart.txt\npython quickstart.py'
};
document.querySelectorAll('[data-os]').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('[data-os]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  document.getElementById('commands').textContent = commands[button.dataset.os];
  document.getElementById('copy-status').textContent = '';
}));
document.getElementById('copy-command')?.addEventListener('click', async () => {
  const source = document.getElementById('commands');
  try {
    await navigator.clipboard.writeText(source.textContent);
    document.getElementById('copy-status').textContent = 'Commands copied. Run them in the extracted repository folder.';
  } catch {
    const range = document.createRange(); range.selectNodeContents(source);
    const selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range);
    document.getElementById('copy-status').textContent = 'Commands selected. Press Ctrl+C or Command+C to copy.';
  }
});
const video = document.getElementById('tutorial-video');
document.querySelectorAll('[data-time]').forEach(button => button.addEventListener('click', async () => {
  document.querySelectorAll('[data-time]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  const seek = () => { video.currentTime = Number(button.dataset.time); };
  if (video.readyState >= 1) seek();
  else { video.addEventListener('loadedmetadata', seek, {once:true}); video.load(); }
  try { await video.play(); document.getElementById('video-status').textContent = ''; }
  catch { document.getElementById('video-status').textContent = 'Chapter selected. Press Play in the video player to continue.'; }
}));
