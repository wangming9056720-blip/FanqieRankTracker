document.addEventListener('DOMContentLoaded', () => {
    const list = document.getElementById('category-list');
    const waterfall = document.getElementById('books-waterfall');
    const title = document.getElementById('current-category-title');
    const date = document.getElementById('update-date');
    const brief = document.getElementById('ai-content');
    const sidebar = document.getElementById('sidebar');
    const menu = document.getElementById('mobile-menu-btn');
    const cache = `v=${Math.floor(Date.now() / 600000)}`;
    let data = null;

    menu.addEventListener('click', () => sidebar.classList.toggle('open'));

    function bookCard(book, rank) {
        const card = document.createElement('article');
        card.className = 'book-card';
        card.innerHTML = `
            <div class="book-rank">${String(rank).padStart(2, '0')}</div>
            <img class="book-cover" src="${book.cover || ''}" alt="${book.title || ''}" loading="lazy">
            <div class="book-info">
                <h3>${book.title || '未知'}</h3>
                <p class="book-author">${book.author || '未知'} · 在读 ${book.reads || '未知'}</p>
                <p class="book-intro">${book.intro || '暂无简介'}</p>
                <a href="${book.url || '#'}" target="_blank" rel="noopener noreferrer">打开番茄详情</a>
            </div>`;
        return card;
    }

    function render(categoryName) {
        const category = categoryName === 'all'
            ? null
            : data.categories.find(item => item.name === categoryName);
        const books = category
            ? category.books
            : data.categories.flatMap(cat => cat.books.map(book => ({...book, _category: cat.name})));

        title.textContent = category ? category.name : '全部分类';
        const trend = category?.trend || {};
        brief.textContent = category
            ? (trend.summary || '阅读榜用于验证成熟市场需求，建议结合新书榜判断供需。')
            : `共${data.categories.length}个分类，${books.length}本阅读榜作品。阅读榜代表30万字以上成熟作品的在读表现。`;
        waterfall.innerHTML = '';
        books.forEach((book, index) => waterfall.appendChild(bookCard(book, index + 1)));

        list.querySelectorAll('li').forEach(node => node.classList.toggle('active', node.dataset.category === (categoryName || 'all')));
        sidebar.classList.remove('open');
    }

    fetch(`api/reading/lastest/all.json?${cache}`)
        .then(response => {
            if (!response.ok) throw new Error('阅读榜接口尚未生成');
            return response.json();
        })
        .then(payload => {
            data = payload;
            date.textContent = `更新：${payload.date || '未知'}`;
            list.innerHTML = '';
            const all = document.createElement('li');
            all.textContent = '全部分类';
            all.dataset.category = 'all';
            all.addEventListener('click', () => render('all'));
            list.appendChild(all);
            payload.categories.forEach(category => {
                const item = document.createElement('li');
                item.textContent = `${category.name} (${category.books.length})`;
                item.dataset.category = category.name;
                item.addEventListener('click', () => render(category.name));
                list.appendChild(item);
            });
            render('all');
        })
        .catch(error => {
            console.error(error);
            list.innerHTML = '<li>暂无数据</li>';
            waterfall.innerHTML = '<p style="padding:24px;color:#f87171">阅读榜首次数据尚未生成。请运行 GitHub Actions 后刷新。</p>';
            brief.textContent = '等待首次阅读榜抓取。';
        });
});
