/* ============================================================
   BYTE — Recipe Social Media Platform
   Main JavaScript v1.0
   Modern ES6+ · No jQuery · Event Delegation · AJAX
   ============================================================ */

'use strict';

// ============================================================
// 1. CSRF TOKEN
// ============================================================

/**
 * Retrieve Django CSRF token from:
 *  1) <meta name="csrf-token"> tag
 *  2) csrftoken cookie (fallback)
 */
const getCSRFToken = () => {
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta) return meta.getAttribute('content');

  // Fallback: read from cookie
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const trimmed = cookie.trim();
    if (trimmed.startsWith('csrftoken=')) {
      return trimmed.substring('csrftoken='.length);
    }
  }
  return '';
};

// ============================================================
// 2. HELPERS
// ============================================================

/**
 * Wrapper around fetch() that automatically adds CSRF and
 * XMLHttpRequest headers for Django compatibility.
 */
const ajaxPost = async (url, body = {}) => {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken(),
      'X-Requested-With': 'XMLHttpRequest',
    },
    credentials: 'same-origin',
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  // Try to parse JSON; if the body is empty, return empty object
  const text = await response.text();
  return text ? JSON.parse(text) : {};
};

/**
 * Wrapper for form-encoded POST (used for comment submission
 * where Django may expect form data).
 */
const ajaxPostForm = async (url, formData) => {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCSRFToken(),
      'X-Requested-With': 'XMLHttpRequest',
    },
    credentials: 'same-origin',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const text = await response.text();
  return text ? JSON.parse(text) : {};
};

/**
 * Show a toast-style message at the top of the page.
 */
const showToast = (message, type = 'info') => {
  let container = document.querySelector('.messages');
  if (!container) {
    container = document.createElement('div');
    container.className = 'messages';
    document.body.prepend(container);
  }

  const toast = document.createElement('div');
  toast.className = `message message-${type}`;
  toast.innerHTML = `
    <span>${message}</span>
    <button class="message-close" aria-label="Close">&times;</button>
  `;
  container.appendChild(toast);

  // Auto-remove after 4s
  const timer = setTimeout(() => toast.remove(), 4000);

  toast.querySelector('.message-close').addEventListener('click', () => {
    clearTimeout(timer);
    toast.remove();
  });
};

/**
 * Animate a count change (increment / decrement).
 */
const updateCount = (el, delta) => {
  if (!el) return;
  const current = parseInt(el.textContent, 10) || 0;
  const next = Math.max(0, current + delta);
  el.textContent = next;
};

// ============================================================
// 3. LIKE SYSTEM
// ============================================================

const handleLike = async (btn) => {
  const recipeId = btn.dataset.recipeId;
  if (!recipeId) return;

  // Optimistic UI
  const isLiked = btn.classList.toggle('liked');
  const countEl = btn.querySelector('.like-count');
  updateCount(countEl, isLiked ? 1 : -1);

  // Trigger pulse animation
  btn.classList.add('pulse');
  btn.addEventListener('animationend', () => btn.classList.remove('pulse'), { once: true });

  try {
    const data = await ajaxPost(`/interactions/like/${recipeId}/`);

    // If server tells us the real state, sync
    if (typeof data.liked === 'boolean') {
      btn.classList.toggle('liked', data.liked);
    }
    if (typeof data.total_likes === 'number' && countEl) {
      countEl.textContent = data.total_likes;
    }
  } catch (err) {
    console.error('Like failed:', err);
    // Revert optimistic UI
    btn.classList.toggle('liked');
    updateCount(countEl, isLiked ? -1 : 1);
    showToast('Could not update like. Please try again.', 'error');
  }
};

// ============================================================
// 4. BOOKMARK SYSTEM
// ============================================================

const handleBookmark = async (btn) => {
  const recipeId = btn.dataset.recipeId;
  if (!recipeId) return;

  const isBookmarked = btn.classList.toggle('bookmarked');
  const countEl = btn.querySelector('.bookmark-count');
  updateCount(countEl, isBookmarked ? 1 : -1);

  try {
    const data = await ajaxPost(`/interactions/bookmark/${recipeId}/`);

    if (typeof data.bookmarked === 'boolean') {
      btn.classList.toggle('bookmarked', data.bookmarked);
    }
    if (typeof data.total_bookmarks === 'number' && countEl) {
      countEl.textContent = data.total_bookmarks;
    }
  } catch (err) {
    console.error('Bookmark failed:', err);
    btn.classList.toggle('bookmarked');
    updateCount(countEl, isBookmarked ? -1 : 1);
    showToast('Could not update bookmark. Please try again.', 'error');
  }
};

// ============================================================
// 5. FOLLOW SYSTEM
// ============================================================

const handleFollow = async (btn) => {
  const userId = btn.dataset.userId;
  if (!userId) return;

  const wasFollowing = btn.classList.contains('following');

  // Optimistic UI
  btn.classList.toggle('following');
  btn.textContent = wasFollowing ? 'Follow' : 'Following';

  // Update follower count on profile if visible
  const followerCountEl = document.querySelector('.follower-count');
  if (followerCountEl) {
    updateCount(followerCountEl, wasFollowing ? -1 : 1);
  }

  try {
    const data = await ajaxPost(`/interactions/follow/${userId}/`);

    if (typeof data.following === 'boolean') {
      btn.classList.toggle('following', data.following);
      btn.textContent = data.following ? 'Following' : 'Follow';
    }
    if (typeof data.followers_count === 'number' && followerCountEl) {
      followerCountEl.textContent = data.followers_count;
    }
  } catch (err) {
    console.error('Follow failed:', err);
    // Revert
    btn.classList.toggle('following');
    btn.textContent = wasFollowing ? 'Following' : 'Follow';
    if (followerCountEl) {
      updateCount(followerCountEl, wasFollowing ? 1 : -1);
    }
    showToast('Could not update follow status. Please try again.', 'error');
  }
};

// ============================================================
// 6. COMMENT SYSTEM
// ============================================================

const handleCommentSubmit = async (form) => {
  const recipeId = form.dataset.recipeId;
  const textarea = form.querySelector('textarea');
  const text = textarea ? textarea.value.trim() : '';

  if (!text || !recipeId) return;

  const submitBtn = form.querySelector('button[type="submit"], .btn-submit');
  if (submitBtn) submitBtn.disabled = true;

  const formData = new FormData();
  formData.append('text', text);

  try {
    const data = await ajaxPostForm(`/interactions/comment/${recipeId}/`, formData);

    // Build and prepend the new comment HTML
    const container = document.getElementById('comments-container');
    if (container && data.comment) {
      const c = data.comment;
      const commentHtml = `
        <div class="comment" data-comment-id="${c.id}">
          <img src="${c.avatar || '/static/images/default-avatar.png'}" alt="" class="avatar">
          <div class="comment-body">
            <div class="comment-header">
              <span class="comment-name">${c.username || 'You'}</span>
              <span class="comment-handle">@${c.handle || ''}</span>
              <span class="comment-time">· just now</span>
              <button class="delete-comment-btn" data-comment-id="${c.id}" title="Delete comment">Delete</button>
            </div>
            <p class="comment-text">${escapeHtml(c.text || text)}</p>
          </div>
        </div>
      `;
      container.insertAdjacentHTML('afterbegin', commentHtml);
    }

    // Clear input
    if (textarea) textarea.value = '';

    // Update comment count
    const commentCount = document.querySelector('.comment-count');
    if (commentCount) {
      updateCount(commentCount, 1);
    }

    showToast('Comment posted!', 'success');
  } catch (err) {
    console.error('Comment submit failed:', err);
    showToast('Could not post comment. Please try again.', 'error');
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
};

const handleCommentDelete = async (btn) => {
  const commentId = btn.dataset.commentId;
  if (!commentId) return;

  if (!confirm('Delete this comment?')) return;

  const commentEl = btn.closest('.comment');

  try {
    await ajaxPost(`/interactions/comment/delete/${commentId}/`);

    if (commentEl) {
      commentEl.style.transition = 'opacity 0.3s ease, max-height 0.3s ease';
      commentEl.style.opacity = '0';
      commentEl.style.maxHeight = '0';
      commentEl.style.overflow = 'hidden';
      setTimeout(() => commentEl.remove(), 300);
    }

    const commentCount = document.querySelector('.comment-count');
    if (commentCount) {
      updateCount(commentCount, -1);
    }

    showToast('Comment deleted.', 'success');
  } catch (err) {
    console.error('Comment delete failed:', err);
    showToast('Could not delete comment. Please try again.', 'error');
  }
};

/**
 * Escape HTML to prevent XSS when inserting user-generated content.
 */
const escapeHtml = (str) => {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
};

// ============================================================
// 7. RATING SYSTEM
// ============================================================

const handleStarRating = async (star) => {
  const ratingContainer = star.closest('.star-rating');
  if (!ratingContainer) return;

  const recipeId = ratingContainer.dataset.recipeId;
  const score = parseInt(star.dataset.score, 10);
  if (!recipeId || !score) return;

  // Optimistic: fill stars up to clicked
  const stars = ratingContainer.querySelectorAll('.star');
  stars.forEach((s) => {
    const sScore = parseInt(s.dataset.score, 10);
    s.classList.toggle('filled', sScore <= score);
  });

  try {
    const data = await ajaxPost(`/interactions/rate/${recipeId}/`, { score });

    // Update average display if returned
    if (typeof data.average_rating === 'number') {
      const avgEl = ratingContainer.querySelector('.average-rating') ||
                    document.querySelector('.average-rating');
      if (avgEl) {
        avgEl.textContent = `${data.average_rating.toFixed(1)} / 5`;
      }
    }

    // Update star display with server value
    if (typeof data.user_rating === 'number') {
      stars.forEach((s) => {
        const sScore = parseInt(s.dataset.score, 10);
        s.classList.toggle('filled', sScore <= data.user_rating);
      });
    }

    showToast('Rating saved!', 'success');
  } catch (err) {
    console.error('Rating failed:', err);
    showToast('Could not save rating. Please try again.', 'error');
  }
};

// Star hover preview
const handleStarHover = (star, isEnter) => {
  const ratingContainer = star.closest('.star-rating');
  if (!ratingContainer) return;

  const stars = ratingContainer.querySelectorAll('.star');
  const hoverScore = parseInt(star.dataset.score, 10);

  stars.forEach((s) => {
    const sScore = parseInt(s.dataset.score, 10);
    if (isEnter) {
      s.classList.toggle('hovered', sScore <= hoverScore);
    } else {
      s.classList.remove('hovered');
    }
  });
};

// ============================================================
// 8. TAB SWITCHING
// ============================================================

const handleTabClick = (tab) => {
  const tabValue = tab.dataset.tab;
  if (!tabValue) return;

  // If the tab has an href, let the browser navigate
  if (tab.tagName === 'A' && tab.getAttribute('href')) return;

  // Otherwise update URL and switch visually
  const url = new URL(window.location);
  url.searchParams.set('tab', tabValue);
  window.history.pushState({}, '', url);

  // Toggle active class
  const container = tab.closest('.feed-tabs, .profile-tabs');
  if (container) {
    container.querySelectorAll('.feed-tab, .profile-tab, .tab').forEach((t) => {
      t.classList.toggle('active', t === tab);
    });
  }
};

// ============================================================
// 9. DARK MODE
// ============================================================

const DARK_MODE_KEY = 'byte-dark-mode';

const applyDarkMode = (enabled) => {
  document.documentElement.classList.toggle('dark-mode', enabled);
  localStorage.setItem(DARK_MODE_KEY, enabled ? '1' : '0');

  // Update toggle button icon if it exists
  const toggleBtn = document.querySelector('.dark-mode-toggle');
  if (toggleBtn) {
    toggleBtn.innerHTML = enabled
      ? '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
      : '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
    toggleBtn.setAttribute('aria-label', enabled ? 'Switch to light mode' : 'Switch to dark mode');
  }
};

const initDarkMode = () => {
  const stored = localStorage.getItem(DARK_MODE_KEY);
  if (stored === '1') {
    applyDarkMode(true);
  } else if (stored === null) {
    // Respect OS preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (prefersDark) applyDarkMode(true);
  }
};

const toggleDarkMode = () => {
  const isCurrentlyDark = document.documentElement.classList.contains('dark-mode');
  applyDarkMode(!isCurrentlyDark);
};

// ============================================================
// 10. SEARCH
// ============================================================

const handleSearchInput = (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    const query = e.target.value.trim();
    if (query) {
      window.location.href = `/search/?q=${encodeURIComponent(query)}`;
    }
  }
};

// ============================================================
// 11. IMAGE PREVIEW
// ============================================================

const handleImagePreview = (input) => {
  const file = input.files[0];
  if (!file) return;

  // Validate file type
  if (!file.type.startsWith('image/')) {
    showToast('Please select a valid image file.', 'warning');
    input.value = '';
    return;
  }

  // Validate file size (max 5MB)
  const maxSize = 5 * 1024 * 1024;
  if (file.size > maxSize) {
    showToast('Image must be smaller than 5 MB.', 'warning');
    input.value = '';
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    // Look for an existing preview container or create one
    let previewContainer = input.closest('.form-group')?.querySelector('.image-preview-container');

    if (!previewContainer) {
      previewContainer = document.createElement('div');
      previewContainer.className = 'image-preview-container';
      input.closest('.form-group')?.appendChild(previewContainer);
    }

    previewContainer.innerHTML = `
      <img src="${e.target.result}" alt="Preview" class="image-preview">
      <button type="button" class="image-preview-remove" aria-label="Remove image">&times;</button>
    `;

    // Remove preview on button click
    previewContainer.querySelector('.image-preview-remove').addEventListener('click', () => {
      previewContainer.innerHTML = '';
      input.value = '';
    });
  };

  reader.readAsDataURL(file);
};

// ============================================================
// 12. NOTIFICATIONS
// ============================================================

const handleMarkAllNotificationsRead = async (btn) => {
  try {
    await ajaxPost('/notifications/mark-all-read/');

    // Remove unread styling from all notifications
    document.querySelectorAll('.notification-item.unread').forEach((item) => {
      item.classList.remove('unread');
    });

    // Remove notification badge
    const badge = document.querySelector('.nav-badge');
    if (badge) badge.remove();

    showToast('All notifications marked as read.', 'success');
  } catch (err) {
    console.error('Mark all read failed:', err);
    showToast('Could not update notifications. Please try again.', 'error');
  }
};

// ============================================================
// 13. FILE UPLOAD DRAG & DROP
// ============================================================

const initFileUploadAreas = () => {
  document.querySelectorAll('.file-upload-area').forEach((area) => {
    const input = area.querySelector('.file-upload-input, input[type="file"]');
    if (!input) return;

    area.addEventListener('dragenter', (e) => {
      e.preventDefault();
      area.classList.add('dragover');
    });

    area.addEventListener('dragover', (e) => {
      e.preventDefault();
      area.classList.add('dragover');
    });

    area.addEventListener('dragleave', () => {
      area.classList.remove('dragover');
    });

    area.addEventListener('drop', (e) => {
      e.preventDefault();
      area.classList.remove('dragover');
      if (e.dataTransfer.files.length > 0) {
        input.files = e.dataTransfer.files;
        // Trigger change event so image preview picks it up
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
  });
};

// ============================================================
// 14. MESSAGE AUTO-DISMISS
// ============================================================

const initMessageAutoDismiss = () => {
  document.querySelectorAll('.message').forEach((msg) => {
    const timer = setTimeout(() => {
      msg.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
      msg.style.opacity = '0';
      msg.style.transform = 'translateY(-12px)';
      setTimeout(() => msg.remove(), 300);
    }, 5000);

    const closeBtn = msg.querySelector('.message-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        clearTimeout(timer);
        msg.remove();
      });
    }
  });
};

// ============================================================
// 15. FOLLOW BUTTON HOVER TEXT
// ============================================================

const initFollowButtonHover = () => {
  // On hover, show "Unfollow" text for .following buttons
  document.addEventListener('mouseenter', (e) => {
    const btn = e.target.closest('.btn-follow.following');
    if (btn) btn.textContent = 'Unfollow';
  }, true);

  document.addEventListener('mouseleave', (e) => {
    const btn = e.target.closest('.btn-follow.following');
    if (btn) btn.textContent = 'Following';
  }, true);
};

// ============================================================
// 16. SHARE BUTTON (Copy Link)
// ============================================================

const handleShare = async (btn) => {
  const recipeId = btn.dataset.recipeId;
  const url = recipeId
    ? `${window.location.origin}/recipes/${recipeId}/`
    : window.location.href;

  try {
    if (navigator.share) {
      await navigator.share({ title: 'Check out this recipe on Byte!', url });
    } else if (navigator.clipboard) {
      await navigator.clipboard.writeText(url);
      showToast('Link copied to clipboard!', 'success');
    }
  } catch (err) {
    // User cancelled or clipboard failed — not critical
    if (err.name !== 'AbortError') {
      console.error('Share failed:', err);
    }
  }
};

// ============================================================
// 17. INFINITE SCROLL / LAZY LOAD (Basic Scaffold)
// ============================================================

// Lightweight intersection observer for future use.
const initLazyImages = () => {
  const images = document.querySelectorAll('img[data-src]');
  if (!images.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.removeAttribute('data-src');
          observer.unobserve(img);
        }
      });
    },
    { rootMargin: '200px' }
  );

  images.forEach((img) => observer.observe(img));
};

// ============================================================
// 18. CHARACTER COUNT FOR TEXTAREAS
// ============================================================

const initCharacterCounters = () => {
  document.querySelectorAll('[data-maxlength]').forEach((el) => {
    const max = parseInt(el.dataset.maxlength, 10);
    if (!max) return;

    // Create counter element
    let counter = el.parentElement?.querySelector('.char-counter');
    if (!counter) {
      counter = document.createElement('span');
      counter.className = 'char-counter text-muted';
      counter.style.cssText = 'font-size:12px; float:right; margin-top:4px;';
      el.parentElement?.appendChild(counter);
    }

    const update = () => {
      const remaining = max - el.value.length;
      counter.textContent = `${remaining} characters remaining`;
      counter.style.color = remaining < 20 ? 'var(--danger-color)' : '';
    };

    el.addEventListener('input', update);
    update();
  });
};

// ============================================================
// 19. GLOBAL EVENT DELEGATION
// ============================================================

const initEventDelegation = () => {
  document.addEventListener('click', (e) => {
    // Like button
    const likeBtn = e.target.closest('.like-btn');
    if (likeBtn) {
      e.preventDefault();
      handleLike(likeBtn);
      return;
    }

    // Bookmark button
    const bookmarkBtn = e.target.closest('.bookmark-btn');
    if (bookmarkBtn) {
      e.preventDefault();
      handleBookmark(bookmarkBtn);
      return;
    }

    // Follow button
    const followBtn = e.target.closest('.follow-btn');
    if (followBtn) {
      e.preventDefault();
      handleFollow(followBtn);
      return;
    }

    // Delete comment
    const deleteCommentBtn = e.target.closest('.delete-comment-btn');
    if (deleteCommentBtn) {
      e.preventDefault();
      handleCommentDelete(deleteCommentBtn);
      return;
    }

    // Star rating
    const starBtn = e.target.closest('.star-rating .star');
    if (starBtn) {
      e.preventDefault();
      handleStarRating(starBtn);
      return;
    }

    // Tab click
    const tabBtn = e.target.closest('.feed-tab, .profile-tab, .tab');
    if (tabBtn) {
      handleTabClick(tabBtn);
      return;
    }

    // Dark mode toggle
    const darkModeBtn = e.target.closest('.dark-mode-toggle');
    if (darkModeBtn) {
      e.preventDefault();
      toggleDarkMode();
      return;
    }

    // Mark all notifications read
    const markReadBtn = e.target.closest('.mark-all-read-btn');
    if (markReadBtn) {
      e.preventDefault();
      handleMarkAllNotificationsRead(markReadBtn);
      return;
    }

    // Share button
    const shareBtn = e.target.closest('.share-btn');
    if (shareBtn) {
      e.preventDefault();
      handleShare(shareBtn);
      return;
    }

    // Image preview remove (delegated)
    const removePreview = e.target.closest('.image-preview-remove');
    if (removePreview) {
      const container = removePreview.closest('.image-preview-container');
      const formGroup = container?.closest('.form-group');
      const input = formGroup?.querySelector('input[type="file"]');
      if (container) container.innerHTML = '';
      if (input) input.value = '';
      return;
    }
  });

  // Star hover events
  document.addEventListener('mouseover', (e) => {
    const star = e.target.closest('.star-rating .star');
    if (star) handleStarHover(star, true);
  });

  document.addEventListener('mouseout', (e) => {
    const star = e.target.closest('.star-rating .star');
    if (star) handleStarHover(star, false);
  });

  // Comment form submit
  document.addEventListener('submit', (e) => {
    const commentForm = e.target.closest('.comment-form');
    if (commentForm) {
      e.preventDefault();
      handleCommentSubmit(commentForm);
      return;
    }
  });

  // Search input Enter key
  document.addEventListener('keydown', (e) => {
    if (e.target.closest('.search-input')) {
      handleSearchInput(e);
    }
  });

  // File input change — image preview
  document.addEventListener('change', (e) => {
    const fileInput = e.target.closest('input[type="file"]');
    if (fileInput && (fileInput.accept?.includes('image') || fileInput.name === 'cover_image' || fileInput.name === 'profile_picture' || fileInput.name === 'image')) {
      handleImagePreview(fileInput);
    }
  });
};

// ============================================================
// 20. SMOOTH SCROLL TO COMMENTS
// ============================================================

const initSmoothScrollLinks = () => {
  document.querySelectorAll('a[href^="#"]').forEach((link) => {
    link.addEventListener('click', (e) => {
      const target = document.querySelector(link.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
};

// ============================================================
// 21. TEXTAREA AUTO-RESIZE
// ============================================================

const initAutoResizeTextareas = () => {
  document.addEventListener('input', (e) => {
    if (e.target.tagName === 'TEXTAREA' && e.target.closest('.comment-form, .compose-box')) {
      const ta = e.target;
      ta.style.height = 'auto';
      ta.style.height = `${ta.scrollHeight}px`;
    }
  });
};

// ============================================================
// 22. INITIALIZATION
// ============================================================

const init = () => {
  initDarkMode();
  initEventDelegation();
  initFileUploadAreas();
  initMessageAutoDismiss();
  initFollowButtonHover();
  initLazyImages();
  initCharacterCounters();
  initSmoothScrollLinks();
  initAutoResizeTextareas();
};

// Run when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
