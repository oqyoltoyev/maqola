// Main JavaScript file for the Articles Website

// Helper function to format dates
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

// Helper function to create article cards dynamically
function createArticleCard(article) {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-lg shadow-md overflow-hidden transition-transform duration-300 hover:shadow-lg hover:-translate-y-1 article-card';
    
    let imageHtml = '';
    if (article.image_url) {
        imageHtml = `<img src="${article.image_url}" alt="${article.title}" class="w-full h-48 object-cover">`;
    } else {
        imageHtml = `
            <div class="w-full h-48 bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-center">
                <span class="text-white text-xl font-semibold">${article.title}</span>
            </div>
        `;
    }
    
    const excerpt = article.content.length > 150 
        ? article.content.substring(0, 150) + '...' 
        : article.content;
    
    card.innerHTML = `
        ${imageHtml}
        <div class="p-6">
            <h3 class="text-xl font-semibold text-gray-900 mb-2">${article.title}</h3>
            <p class="text-gray-600 mb-4">${excerpt}</p>
            <div class="flex items-center justify-between">
                <span class="text-sm text-gray-500">${formatDate(article.created_at)}</span>
                <span class="text-sm text-gray-500">${article.views} views</span>
            </div>
            <a href="/articles/${article.id}" class="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                Read More
            </a>
        </div>
    `;
    
    return card;
}

// Calculate reading time for articles
function calculateReadingTime() {
    const articleContent = document.querySelector('.article-content');
    if (articleContent) {
        const text = articleContent.textContent || articleContent.innerText;
        const wordCount = text.split(/\s+/).length;
        const readingTime = Math.ceil(wordCount / 200); // Assuming 200 words per minute
        
        const readingTimeElement = document.getElementById('reading-time');
        if (readingTimeElement) {
            readingTimeElement.textContent = `${readingTime} min read`;
        }
    }
}

// Handle search functionality
function setupSearch() {
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');
    
    if (searchInput && searchResults) {
        searchInput.addEventListener('input', debounce(async (e) => {
            const query = e.target.value.trim();
            
            if (query.length < 2) {
                searchResults.innerHTML = '';
                searchResults.classList.add('hidden');
                return;
            }
            
            try {
                const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                
                searchResults.innerHTML = '';
                
                if (data.length === 0) {
                    searchResults.innerHTML = `
                        <div class="p-4 text-center text-gray-500">
                            No results found for "${query}"
                        </div>
                    `;
                } else {
                    data.forEach(article => {
                        const resultItem = document.createElement('a');
                        resultItem.href = `/articles/${article.id}`;
                        resultItem.className = 'block p-4 hover:bg-gray-50 border-b border-gray-100';
                        resultItem.innerHTML = `
                            <h4 class="font-medium text-gray-900">${article.title}</h4>
                            <p class="text-sm text-gray-500 mt-1">${article.content.substring(0, 100)}...</p>
                        `;
                        searchResults.appendChild(resultItem);
                    });
                }
                
                searchResults.classList.remove('hidden');
            } catch (error) {
                console.error('Search error:', error);
            }
        }, 300));
        
        // Hide search results when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.classList.add('hidden');
            }
        });
    }
}

// Debounce function to limit API calls
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    calculateReadingTime();
    setupSearch();
    
    // Mobile menu toggle
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }
    
    // Add animation to article cards
    const articleCards = document.querySelectorAll('.article-card');
    articleCards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
    });
});
