// ThoughtsNPairs — vanilla JS

// Star picker: AJAX rating
document.addEventListener('DOMContentLoaded', function () {
  const picker = document.getElementById('star-picker');
  if (!picker) return;

  const pairingId = document.getElementById('rating-widget').dataset.pairingId;
  const buttons = picker.querySelectorAll('.star-btn');
  const avgStars = document.getElementById('avg-stars');
  const avgNumber = document.getElementById('avg-number');

  // Hover highlight
  buttons.forEach(function (btn, idx) {
    btn.addEventListener('mouseenter', function () {
      buttons.forEach(function (b, i) {
        b.style.color = i <= idx ? 'var(--accent)' : 'var(--border)';
      });
    });
    btn.addEventListener('mouseleave', function () {
      buttons.forEach(function (b) {
        b.style.color = '';
      });
    });
    btn.addEventListener('click', function () {
      const score = parseInt(btn.dataset.score);
      submitRating(pairingId, score, buttons, avgStars, avgNumber);
    });
  });
});

function submitRating(pairingId, score, buttons, avgStars, avgNumber) {
  fetch('/api/rate/' + pairingId, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ score: score }),
    credentials: 'same-origin'
  })
  .then(function (res) {
    if (res.status === 401) {
      window.location.href = '/register?next=' + window.location.pathname;
      return;
    }
    return res.json();
  })
  .then(function (data) {
    if (!data) return;
    // Update UI
    if (avgStars) avgStars.textContent = data.stars;
    if (avgNumber) avgNumber.textContent = data.avg_rating;
    buttons.forEach(function (b, i) {
      if (i < data.user_score) {
        b.classList.add('star-btn--filled');
      } else {
        b.classList.remove('star-btn--filled');
      }
    });
  })
  .catch(function (err) {
    console.error('Rating failed:', err);
  });
}
