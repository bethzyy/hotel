/**
 * Hotel Search Application - Main JavaScript
 */

// API Base URL
const API_BASE = '/api';

// ==================== Utility Functions ====================

/**
 * Show loading overlay
 */
function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

/**
 * Hide loading overlay
 */
function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

/**
 * Adjust numeric input value
 */
function adjustValue(inputId, delta) {
    const input = document.getElementById(inputId);
    const currentValue = parseInt(input.value) || 0;
    const minValue = parseInt(input.min) || 0;
    const maxValue = parseInt(input.max) || 100;

    let newValue = currentValue + delta;
    newValue = Math.max(minValue, Math.min(maxValue, newValue));

    input.value = newValue;

    // Trigger change event
    const event = new Event('change', { bubbles: true });
    input.dispatchEvent(event);
}

/**
 * Format date for display
 */
function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const options = { month: 'short', day: 'numeric' };
    return date.toLocaleDateString('zh-CN', options);
}

/**
 * Format currency
 */
function formatCurrency(amount, currency = 'CNY') {
    if (amount === null || amount === undefined) return '询价';
    const symbols = {
        'CNY': '¥',
        'USD': '$',
        'EUR': '€',
        'JPY': '¥'
    };
    return `${symbols[currency] || '¥'}${amount.toLocaleString()}`;
}

// ==================== Favorites Functions ====================

/**
 * Load favorites count
 */
async function loadFavoritesCount() {
    try {
        const response = await fetch(`${API_BASE}/favorites`);
        const result = await response.json();

        if (result.success) {
            const count = result.data.total || 0;
            const badge = document.getElementById('favoritesCount');
            if (badge) {
                badge.textContent = count;
                badge.style.display = count > 0 ? 'inline-block' : 'none';
            }
        }
    } catch (error) {
        console.error('Load favorites count error:', error);
    }
}

/**
 * Toggle favorite status
 */
async function toggleFavoriteStatus(hotelId, hotelData, iconElement) {
    try {
        const response = await fetch(`${API_BASE}/favorites/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                hotel_id: hotelId,
                hotel_data: hotelData
            })
        });

        const result = await response.json();

        if (result.success) {
            const isFavorite = result.data.is_favorite;
            if (isFavorite) {
                iconElement.className = 'bi bi-heart-fill text-danger';
            } else {
                iconElement.className = 'bi bi-heart';
            }
            loadFavoritesCount();
            return isFavorite;
        }
    } catch (error) {
        console.error('Toggle favorite error:', error);
    }
    return null;
}

// ==================== Search History Functions ====================

/**
 * Load search history
 */
async function loadSearchHistory() {
    try {
        const response = await fetch(`${API_BASE}/history?limit=5`);
        const result = await response.json();

        if (result.success && result.data.history.length > 0) {
            const historySection = document.getElementById('historySection');
            const historyList = document.getElementById('historyList');

            if (historySection && historyList) {
                historySection.style.display = 'block';
                historyList.innerHTML = result.data.history.map(item => `
                    <span class="badge bg-light text-dark" onclick="useHistoryItem('${item.place}', '${item.place_type || 'attraction'}')">
                        <i class="bi bi-clock"></i> ${item.place}
                    </span>
                `).join('');
            }
        }
    } catch (error) {
        console.error('Load search history error:', error);
    }
}

/**
 * Use history item to fill search form
 */
function useHistoryItem(place, placeType) {
    const placeInput = document.getElementById('place');
    const placeTypeSelect = document.getElementById('placeType');

    if (placeInput) placeInput.value = place;
    if (placeTypeSelect) placeTypeSelect.value = placeType;
}

// ==================== Place Types Functions ====================

/**
 * Load available place types
 */
async function loadPlaceTypes() {
    try {
        const response = await fetch(`${API_BASE}/place-types`);
        const result = await response.json();

        if (result.success) {
            return result.data.place_types;
        }
    } catch (error) {
        console.error('Load place types error:', error);
    }
    return [];
}

// ==================== Tags Functions ====================

/**
 * Load available tags
 */
async function loadTags() {
    try {
        const response = await fetch(`${API_BASE}/tags`);
        const result = await response.json();

        if (result.success) {
            return result.data.tags;
        }
    } catch (error) {
        console.error('Load tags error:', error);
    }
    return [];
}

// ==================== Form Validation ====================

/**
 * Validate search form
 */
function validateSearchForm() {
    const place = document.getElementById('place')?.value?.trim();
    const placeType = document.getElementById('placeType')?.value;

    if (!place) {
        alert('请输入目的地');
        return false;
    }

    if (!placeType) {
        alert('请选择地点类型');
        return false;
    }

    return true;
}

// ==================== Error Handling ====================

/**
 * Show error message
 */
function showError(message, containerId = 'errorMessage') {
    const container = document.getElementById(containerId);
    if (container) {
        const errorText = document.getElementById('errorText') || container;
        errorText.textContent = message;
        container.style.display = 'block';

        // Auto hide after 5 seconds
        setTimeout(() => {
            container.style.display = 'none';
        }, 5000);
    }
}

/**
 * Hide error message
 */
function hideError(containerId = 'errorMessage') {
    const container = document.getElementById(containerId);
    if (container) {
        container.style.display = 'none';
    }
}

// ==================== Local Storage Helpers ====================

/**
 * Save search to local storage
 */
function saveSearchToLocal(place, placeType) {
    try {
        let recentSearches = JSON.parse(localStorage.getItem('recentSearches') || '[]');

        // Remove duplicate
        recentSearches = recentSearches.filter(s => s.place !== place);

        // Add new search
        recentSearches.unshift({
            place: place,
            placeType: placeType,
            timestamp: Date.now()
        });

        // Keep only 10 recent searches
        recentSearches = recentSearches.slice(0, 10);

        localStorage.setItem('recentSearches', JSON.stringify(recentSearches));
    } catch (error) {
        console.error('Save search to local error:', error);
    }
}

/**
 * Get recent searches from local storage
 */
function getRecentSearchesFromLocal() {
    try {
        return JSON.parse(localStorage.getItem('recentSearches') || '[]');
    } catch (error) {
        return [];
    }
}

// ==================== Initialization ====================

/**
 * Initialize common functionality
 */
function initCommon() {
    // Load favorites count
    loadFavoritesCount();

    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(el => new bootstrap.Tooltip(el));
}

// Run initialization when DOM is ready
document.addEventListener('DOMContentLoaded', initCommon);


// ==================== Provider Functions ====================

/**
 * Get available providers
 */
async function getProviders() {
    try {
        const response = await fetch(`${API_BASE}/providers`);
        const result = await response.json();

        if (result.success) {
            return result.data.providers;
        }
    } catch (error) {
        console.error('Get providers error:', error);
    }
    return [];
}

/**
 * Get provider info by name
 */
async function getProviderInfo(providerName) {
    const providers = await getProviders();
    return providers.find(p => p.id === providerName);
}

/**
 * Check if provider supports booking
 */
function providerSupportsBooking(providerName) {
    return providerName === 'tuniu';
}

/**
 * Check if provider supports pagination
 */
function providerSupportsPagination(providerName) {
    return providerName === 'tuniu';
}


// ==================== Booking Functions ====================

/**
 * Prepare booking for a room
 */
async function prepareBooking(hotelId, roomId, checkIn, checkOut, provider = 'tuniu') {
    try {
        const response = await fetch(`${API_BASE}/book/prepare`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                provider: provider,
                hotel_id: hotelId,
                room_id: roomId,
                check_in: checkIn,
                check_out: checkOut
            })
        });

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Prepare booking error:', error);
        return { success: false, error: '网络错误' };
    }
}

/**
 * Create a booking order
 */
async function createBooking(bookingData) {
    try {
        const response = await fetch(`${API_BASE}/book/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(bookingData)
        });

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Create booking error:', error);
        return { success: false, error: '网络错误' };
    }
}


// ==================== Multi-Provider Search Helpers ====================

/**
 * Build search params for provider
 */
function buildSearchParams(provider, formData) {
    if (provider === 'tuniu') {
        return {
            provider: 'tuniu',
            city_name: formData.city_name,
            check_in: formData.check_in,
            check_out: formData.check_out,
            adult_count: formData.adult_count || 2,
            child_count: formData.child_count || 0,
            keyword: formData.keyword || null,
            page_num: formData.page_num || 1,
            query_id: formData.query_id || null
        };
    } else {
        // RollingGo
        return {
            provider: 'rollinggo',
            query: `Find hotels near ${formData.place}`,
            place: formData.place,
            place_type: formData.place_type,
            check_in_date: formData.check_in_date || null,
            stay_nights: formData.stay_nights || 1,
            adult_count: formData.adult_count || 2,
            child_count: formData.child_count || 0,
            child_ages: formData.child_ages || [],
            star_ratings: formData.star_ratings || null,
            max_price: formData.max_price || null,
            distance: formData.distance || null,
            size: formData.size || 20
        };
    }
}

/**
 * Store search params for detail page
 */
function storeDetailSearchParams(searchParams) {
    sessionStorage.setItem('detailSearchParams', JSON.stringify(searchParams));
}

/**
 * Get stored search params
 */
function getDetailSearchParams() {
    const params = sessionStorage.getItem('detailSearchParams');
    return params ? JSON.parse(params) : null;
}


// ==================== Date Utilities ====================

/**
 * Get tomorrow's date string
 */
function getTomorrowDate() {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
}

/**
 * Get date after n days
 */
function getDateAfterDays(startDate, days) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + days);
    return date.toISOString().split('T')[0];
}

/**
 * Calculate nights between two dates
 */
function calculateNights(checkIn, checkOut) {
    const checkInDate = new Date(checkIn);
    const checkOutDate = new Date(checkOut);
    const diffTime = Math.abs(checkOutDate - checkInDate);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
}


// ==================== Validation Utilities ====================

/**
 * Validate phone number (Chinese mobile)
 */
function validatePhoneNumber(phone) {
    return /^1[3-9]\d{9}$/.test(phone);
}

/**
 * Validate date format (YYYY-MM-DD)
 */
function validateDateFormat(dateStr) {
    return /^\d{4}-\d{2}-\d{2}$/.test(dateStr);
}

/**
 * Validate check-in/out dates
 */
function validateDates(checkIn, checkOut) {
    if (!validateDateFormat(checkIn) || !validateDateFormat(checkOut)) {
        return { valid: false, error: '日期格式不正确' };
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const checkInDate = new Date(checkIn);
    const checkOutDate = new Date(checkOut);

    if (checkInDate < today) {
        return { valid: false, error: '入住日期不能早于今天' };
    }

    if (checkOutDate <= checkInDate) {
        return { valid: false, error: '离店日期必须晚于入住日期' };
    }

    return { valid: true };
}
