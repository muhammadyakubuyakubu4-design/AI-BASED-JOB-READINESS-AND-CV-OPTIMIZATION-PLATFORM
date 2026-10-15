/* =====================================================
   CareerAI - Main JavaScript
   ===================================================== */

document.addEventListener('DOMContentLoaded', function () {

  // ===================== SIDEBAR TOGGLE =====================
  const sidebar = document.getElementById('sidebar');
  const mainWrapper = document.getElementById('mainWrapper');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebarClose = document.getElementById('sidebarClose');
  const sidebarOverlay = document.getElementById('sidebarOverlay');

  function openSidebar() {
    if (window.innerWidth < 992) {
      sidebar && sidebar.classList.add('mobile-open');
      sidebarOverlay && sidebarOverlay.classList.add('active');
    } else {
      sidebar && sidebar.classList.toggle('collapsed');
      mainWrapper && mainWrapper.classList.toggle('sidebar-collapsed');
      localStorage.setItem('sidebar_collapsed', sidebar.classList.contains('collapsed'));
    }
  }

  function closeSidebar() {
    sidebar && sidebar.classList.remove('mobile-open');
    sidebarOverlay && sidebarOverlay.classList.remove('active');
  }

  sidebarToggle && sidebarToggle.addEventListener('click', openSidebar);
  sidebarClose && sidebarClose.addEventListener('click', closeSidebar);
  sidebarOverlay && sidebarOverlay.addEventListener('click', closeSidebar);

  // Restore collapsed state on desktop
  if (window.innerWidth >= 992 && localStorage.getItem('sidebar_collapsed') === 'true') {
    sidebar && sidebar.classList.add('collapsed');
    mainWrapper && mainWrapper.classList.add('sidebar-collapsed');
  }

  // ===================== DARK MODE TOGGLE =====================
  const themeToggle = document.getElementById('themeToggle');
  const themeIcon = document.getElementById('themeIcon');
  const htmlEl = document.documentElement;

  function applyTheme(theme) {
    htmlEl.setAttribute('data-bs-theme', theme);
    if (themeIcon) {
      themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
    localStorage.setItem('theme', theme);
  }

  // Apply saved theme
  const savedTheme = localStorage.getItem('theme') || 'light';
  applyTheme(savedTheme);

  themeToggle && themeToggle.addEventListener('click', function () {
    const current = htmlEl.getAttribute('data-bs-theme');
    applyTheme(current === 'dark' ? 'light' : 'dark');
  });

  // ===================== CHATBOT =====================
  const chatbotTrigger = document.getElementById('chatbotTrigger');
  const chatbotWidget = document.getElementById('chatbotWidget');
  const chatbotClose = document.getElementById('chatbotClose');
  const chatbotInput = document.getElementById('chatbotInput');
  const chatbotSend = document.getElementById('chatbotSend');
  const chatbotMessages = document.getElementById('chatbotMessages');
  const chatbotBadge = document.getElementById('chatbotBadge');

  let chatOpen = false;
  let chatHistory = [];

  function toggleChat() {
    chatOpen = !chatOpen;
    chatbotWidget && chatbotWidget.classList.toggle('open', chatOpen);
    if (chatOpen && chatbotBadge) {
      chatbotBadge.style.display = 'none';
    }
    if (chatOpen && chatbotInput) {
      setTimeout(() => chatbotInput.focus(), 300);
    }
  }

  chatbotTrigger && chatbotTrigger.addEventListener('click', toggleChat);
  chatbotClose && chatbotClose.addEventListener('click', toggleChat);

  function appendMessage(text, isUser) {
    if (!chatbotMessages) return;
    const msg = document.createElement('div');
    msg.className = 'chat-message ' + (isUser ? 'user-message' : 'bot-message');
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    bubble.textContent = text;
    msg.appendChild(bubble);
    chatbotMessages.appendChild(msg);
    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
  }

  function showTyping() {
    if (!chatbotMessages) return null;
    const typing = document.createElement('div');
    typing.className = 'chat-message bot-message';
    typing.id = 'typing-indicator';
    typing.innerHTML = '<div class="chat-bubble chat-typing"><div class="typing-dots"><span></span><span></span><span></span></div></div>';
    chatbotMessages.appendChild(typing);
    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    return typing;
  }

  async function sendChatMessage() {
    if (!chatbotInput) return;
    const message = chatbotInput.value.trim();
    if (!message) return;

    chatHistory.push({ role: 'user', content: message });
    appendMessage(message, true);
    chatbotInput.value = '';

    const typing = showTyping();

    let csrfToken = getCookie('csrftoken');
    if (!csrfToken) {
      const meta = document.querySelector('meta[name="csrf-token"]');
      if (meta) csrfToken = meta.getAttribute('content');
    }

    try {
      const endpoints = ['/interview/chat/', '/career/chatbot/'];
      let response = null;
      let lastError = '';

      for (const endpoint of endpoints) {
        try {
          response = await fetch(endpoint, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrfToken || '',
            },
            body: JSON.stringify({ message, history: chatHistory }),
          });
          if (response.ok) break;
          lastError = 'Server returned ' + response.status;
          const errData = await response.json().catch(() => null);
          if (errData && errData.error) lastError = errData.error;
        } catch (e) {
          lastError = e.message || 'Network error';
          continue;
        }
      }

      typing && typing.remove();

      if (response && response.ok) {
        const data = await response.json();
        const reply = data.response || 'I received your message!';
        chatHistory.push({ role: 'assistant', content: reply });
        appendMessage(reply, false);
      } else {
        const errMsg = lastError || 'Unable to reach server';
        appendMessage("Sorry, I couldn't process that. (" + errMsg + ")", false);
      }
    } catch (error) {
      typing && typing.remove();
      appendMessage("Connection error. Please try again.", false);
    }
  }

  chatbotSend && chatbotSend.addEventListener('click', sendChatMessage);
  chatbotInput && chatbotInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  });

  // ===================== NOTIFICATION POLLING =====================
  function pollNotifications() {
    fetch('/notifications/api/count/')
      .then(r => r.json())
      .then(data => {
        const badges = document.querySelectorAll('.action-badge, .nav-badge');
        badges.forEach(b => {
          if (data.count > 0) {
            b.textContent = data.count;
            b.style.display = '';
          } else {
            b.style.display = 'none';
          }
        });
      })
      .catch(() => {});
  }

  // Poll every 60 seconds
  if (document.getElementById('notifDropdown')) {
    setInterval(pollNotifications, 60000);
  }

  // ===================== FORM INPUT STYLING =====================
  // Add Bootstrap classes to Django form fields
  document.querySelectorAll('input:not([type="checkbox"]):not([type="radio"]):not([type="file"]):not([type="hidden"]):not(.chatbot-input)').forEach(function (el) {
    if (!el.classList.contains('form-control') && !el.classList.contains('btn')) {
      el.classList.add('form-control');
    }
  });

  document.querySelectorAll('select').forEach(function (el) {
    if (!el.classList.contains('form-select')) {
      el.classList.add('form-select');
    }
  });

  document.querySelectorAll('textarea').forEach(function (el) {
    if (!el.classList.contains('form-control')) {
      el.classList.add('form-control');
      el.rows = el.rows || 5;
    }
  });

  // ===================== SCROLL ANIMATIONS =====================
  const animateEls = document.querySelectorAll('.feature-card, .step-card, .stat-card, .testimonial-card');
  if (animateEls.length && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    animateEls.forEach(el => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(24px)';
      el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      observer.observe(el);
    });
  }

  // ===================== PROGRESS BAR ANIMATION =====================
  document.querySelectorAll('.progress-bar').forEach(function (bar) {
    const width = bar.style.width;
    bar.style.width = '0';
    setTimeout(() => { bar.style.width = width; }, 300);
  });

  // ===================== TOOLTIP INIT =====================
  const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipEls.forEach(el => new bootstrap.Tooltip(el));

  // ===================== CONFIRM DIALOGS =====================
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // ===================== AUTO-HIDE ALERTS =====================
  setTimeout(function () {
    document.querySelectorAll('.alert:not(.alert-permanent)').forEach(function (el) {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      if (bsAlert) bsAlert.close();
    });
  }, 6000);

});

// ===================== CSRF HELPER =====================
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
