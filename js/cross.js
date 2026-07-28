document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('cross-grid');
    const summary = document.getElementById('cross-summary');
    const cache = `v=${Math.floor(Date.now() / 600000)}`;

    const chips = items => {
        if (!items || !items.length) return '<span class="chip">暂无明显信号</span>';
        return items.map(item => `<span class="chip">${item.keyword} · ${item.count}</span>`).join('');
    };

    fetch(`api/cross/lastest/all.json?${cache}`)
        .then(response => {
            if (!response.ok) throw new Error('交叉分析接口尚未生成');
            return response.json();
        })
        .then(data => {
            summary.textContent = `新书榜数据 ${data.new_rank_date}，阅读榜数据 ${data.reading_rank_date}。两榜共振用于确认需求，新书独有用于观察风向，阅读榜独有用于寻找成熟市场中的供给空位。`;
            grid.innerHTML = '';
            data.categories.forEach(category => {
                const card = document.createElement('article');
                card.className = 'cross-card';
                card.innerHTML = `
                    <h3>${category.name}</h3>
                    <div class="signal-row"><strong>双榜验证</strong><div class="chips">${chips(category.verified_keywords)}</div></div>
                    <div class="signal-row"><strong>新书正在冒头</strong><div class="chips">${chips(category.emerging_keywords)}</div></div>
                    <div class="signal-row"><strong>成熟需求 / 新书较少</strong><div class="chips">${chips(category.mature_keywords)}</div></div>
                    <div class="book-lines"><b>新书榜头部：</b>${(category.new_top_books || []).join('、') || '无'}</div>
                    <div class="book-lines"><b>阅读榜头部：</b>${(category.reading_top_books || []).join('、') || '无'}</div>`;
                grid.appendChild(card);
            });
        })
        .catch(error => {
            console.error(error);
            summary.textContent = '等待首次阅读榜抓取和交叉分析。';
            grid.innerHTML = '<p style="padding:24px;color:#f87171">请先运行更新后的 GitHub Actions。</p>';
        });
});
