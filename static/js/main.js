/**
 * LOSTLINK - Main Frontend JavaScript
 * Mobile navbar, toast alerts, image preview, demo credentials helper
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Mobile Menu Toggle
  const toggleBtn = document.querySelector('.mobile-toggle');
  const navLinks = document.querySelector('.nav-links');
  if (toggleBtn && navLinks) {
    toggleBtn.addEventListener('click', function () {
      navLinks.classList.toggle('show');
    });
  }

  // 2. Auto-Dismiss Flash Alerts after 5 seconds
  const flashAlerts = document.querySelectorAll('.flash-container .alert');
  flashAlerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateX(50px)';
      setTimeout(() => alert.remove(), 400);
    }, 5000);
  });

  // 3. Image Upload Preview Handler
  const imageInput = document.getElementById('image');
  const previewImg = document.getElementById('previewImage');
  const uploadWrapper = document.getElementById('imageUploadWrapper');

  if (imageInput && previewImg) {
    imageInput.addEventListener('change', function () {
      const file = this.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
          previewImg.src = e.target.result;
          previewImg.style.display = 'block';
          if (uploadWrapper) {
            const promptText = uploadWrapper.querySelector('.upload-prompt');
            if (promptText) promptText.style.display = 'none';
          }
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // 4. Modal Helpers
  window.openModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('show');
      document.body.style.overflow = 'hidden';
    }
  };

  window.closeModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('show');
      document.body.style.overflow = '';
    }
  };

  // Close modal when clicking on backdrop
  document.querySelectorAll('.modal-backdrop').forEach(modal => {
    modal.addEventListener('click', function (e) {
      if (e.target === this) {
        this.classList.remove('show');
        document.body.style.overflow = '';
      }
    });
  });

  // 5. Viva Demo 1-Click Credentials Filler for Login Page
  window.fillDemoCredentials = function (role) {
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    if (emailInput && passwordInput) {
      if (role === 'admin') {
        emailInput.value = 'admin@lostlink.com';
        passwordInput.value = 'admin123';
      } else {
        emailInput.value = 'rahul@lostlink.com';
        passwordInput.value = 'user123';
      }
      emailInput.focus();
    }
  };

  // 6. Copy Item Share URL
  window.copyItemLink = function () {
    navigator.clipboard.writeText(window.location.href).then(() => {
      alert('Item link copied to clipboard!');
    }).catch(err => {
      prompt('Copy this link:', window.location.href);
    });
  };
});
