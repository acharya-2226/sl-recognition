var toggle = document.getElementById('navToggle');
var sidebar = document.getElementById('sidebar');

if (toggle && sidebar) {
  toggle.addEventListener('click', function () {
    sidebar.classList.toggle('open');
  });
}

function getCsrfToken() {
  var tokenInput = document.querySelector('[name="csrfmiddlewaretoken"]');
  if (tokenInput) return tokenInput.value;
  var match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
  return match ? match[1] : '';
}

function setFeedback(message, className) {
  var feedback = document.getElementById('feedback');
  if (!feedback) return;
  feedback.textContent = message;
  feedback.className = 'feedback ' + className;
}

var roundDataElement = document.getElementById('practice-round-data');
var questionNumber = document.getElementById('question-number');
var questionImage = document.getElementById('question-image');
var questionSymbol = document.getElementById('question-symbol');
var choicesContainer = document.getElementById('choices');
var scoreDisplay = document.getElementById('score-display');
var practiceCard = document.querySelector('.practice-round .practice-card');
var studyNote = document.querySelector('.practice-round .study-note');
var practiceResult = document.getElementById('practice-result');
var finalScore = document.getElementById('final-score');
var roundData = [];
var currentQuestionIndex = 0;
var score = 0;
var waitingForNext = false;

if (roundDataElement) {
  try {
    roundData = JSON.parse(roundDataElement.textContent || '[]');
  } catch (error) {
    console.error('Could not read practice round data.', error);
  }
}

function renderQuestion(question) {
  questionNumber.textContent = String(currentQuestionIndex + 1);
  setFeedback('', '');

  if (question.image) {
    questionImage.src = question.image;
    questionImage.hidden = false;
    questionSymbol.hidden = true;
  } else {
    questionImage.src = '';
    questionImage.hidden = true;
    questionSymbol.textContent = '✋';
    questionSymbol.hidden = false;
  }

  choicesContainer.innerHTML = '';
  question.choices.forEach(function (choice) {
    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'choice';
    button.setAttribute('data-choice-id', choice.id);
    button.innerHTML = '<b>' + String(choice.title).slice(0, 1) + '</b>' + choice.title;
    button.addEventListener('click', handleChoice);
    choicesContainer.appendChild(button);
  });
}

function finishRound() {
  if (practiceCard) practiceCard.hidden = true;
  if (studyNote) studyNote.hidden = true;
  if (practiceResult) practiceResult.hidden = false;
  if (finalScore) finalScore.textContent = score + ' / 5';
}

function showNextQuestion() {
  currentQuestionIndex += 1;
  if (currentQuestionIndex >= roundData.length) {
    finishRound();
    return;
  }

  renderQuestion(roundData[currentQuestionIndex]);
  waitingForNext = false;
}

function handleChoice(event) {
  if (waitingForNext) return;
  waitingForNext = true;

  var button = event.currentTarget;
  var buttons = choicesContainer.querySelectorAll('.choice');
  var selectedId = button.getAttribute('data-choice-id');
  var question = roundData[currentQuestionIndex];
  var isCorrect = String(question.question_id) === String(selectedId);

  buttons.forEach(function (item) { item.disabled = true; });
  button.classList.add(isCorrect ? 'correct' : 'wrong');

  if (isCorrect) {
    score += 1;
    setFeedback('Correct — congratulations! You earned 1 mark.', 'correct');
  } else {
    setFeedback('Wrong answer. The correct answer is ' + question.title + '.', 'wrong');
  }

  scoreDisplay.textContent = 'Score: ' + score + ' / 5';
  window.setTimeout(showNextQuestion, 1500);
}

if (roundData.length && choicesContainer) {
  renderQuestion(roundData[0]);
}

document.querySelectorAll('.validate-btn').forEach(function (button) {
  button.addEventListener('click', function () {
    fetch(button.getAttribute('data-url'), {
      method: 'POST',
      headers: { 'X-CSRFToken': getCsrfToken() }
    })
      .then(function (response) { return response.json(); })
      .then(function (data) { window.alert(data.message); })
      .catch(function (error) { console.error(error); });
  });
});
