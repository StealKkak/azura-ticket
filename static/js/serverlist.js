//v2.1
const serverListEl = document.getElementById('server-list');
const loadingBar = document.getElementById('loading-bar');
const refreshButton = document.getElementById('refresh-server');

function createServerCard(server) {
    const col = document.createElement('div');
    col.className = 'col-12 col-md-6 col-lg-4';

    const card = document.createElement('div');
    card.className = 'card h-100 text-center shadow-sm';

    const img = document.createElement('img');
    img.src = server.icon 
    ? `https://cdn.discordapp.com/icons/${server.id}/${server.icon}.${server.icon.startsWith('a_') ? 'gif' : 'png'}` 
    : 'https://via.placeholder.com/80?text=No+Icon';
    img.alt = server.name + " 아이콘";
    img.className = 'card-img-top rounded-circle mx-auto mt-3';
    img.style.width = '80px';
    img.style.height = '80px';
    img.style.objectFit = 'cover';

    const cardBody = document.createElement('div');
    cardBody.className = 'card-body d-flex flex-column';

    const title = document.createElement('h5');
    title.className = 'card-title';
    title.textContent = server.name;

    const btn = document.createElement('button');
    btn.className = 'btn btn-primary mt-auto';
    btn.textContent = '서버로 이동';
    btn.onclick = () => {
    window.location.href = `/dashboard/${server.id}`;
    };

    cardBody.appendChild(title);
    cardBody.appendChild(btn);

    card.appendChild(img);
    card.appendChild(cardBody);
    col.appendChild(card);

    return col;
}

async function loadServers() {
    try {
        refreshButton.disabled = true;
        loadingBar.style.display = 'block';
        const res = await fetch('/api/users/me/guilds');
        const data = await res.json();

        if (!res.ok) {
            const error = data.error || '서버 목록을 불러오는 중 오류가 발생했습니다';
            if (error === "Unauthorized") {
                alert("로그인 후 사용해주세요!");
                window.location.href = "/";
                return;
            } else if (error === "No Data Found") {
                alert("티켓봇을 사용중인 서버 중 관리자인 서버가 없습니다.");
                renderServers([]);
                return;
            } else if (error === "Refresh token expired") {
                alert("리프레시 토큰이 만료되었습니다! 디스코드로 로그인해주세요!");
                window.location.href = "/logout";
                return;
            } else {
                alert(error);
                return;
            }
        }

        renderServers(data.data);
    } catch (err) {
        console.error('서버 목록 로드 실패:', err);
        alert('서버 목록을 불러오는 중 오류가 발생했습니다.');
    } finally {
        refreshButton.disabled = false;
        loadingBar.style.display = 'none';
    }
}

async function refreshServers() {
    try {
    refreshButton.disabled = true;
    loadingBar.style.display = 'block';

    const res = await fetch('/api/users/me/guilds?refresh=true');
    const data = await res.json();

    if (!res.ok) {
        const error = data.error || '서버 목록을 불러오는 중 오류가 발생했습니다';
        if (error === "UnAuthorized") {
            alert("로그인 후 사용해주세요!");
            window.location.href = "/login";
            return;
        } else if (error === "No Data Found") {
            alert("티켓봇을 사용중인 서버 중 관리자인 서버가 없습니다.");
            renderServers([]);
            return;
        } else if (error === "Refresh token expired") {
            alert("리프레시 토큰이 만료되었습니다! 다시 로그인해주세요!");
            window.location.href = "/logout";
            return;
        } else {
            alert(error);
            return;
        }
    }

    renderServers(data.data);
        } catch (err) {
            console.error('서버 새로고침 실패:', err);
            alert('서버 새로고침 중 오류가 발생했습니다.');
        } finally {
            refreshButton.disabled = false;
            loadingBar.style.display = 'none';
        }
}

function renderServers(guilds) {
    serverListEl.innerHTML = '';
    if (guilds.length === 0) {
        serverListEl.innerHTML = '<p class="text-center text-muted">서버가 없습니다.</p>';
        return;
    }
    guilds.forEach(server => {
        const card = createServerCard(server);
        serverListEl.appendChild(card);
    });
}

refreshButton.addEventListener('click', refreshServers);

loadServers();