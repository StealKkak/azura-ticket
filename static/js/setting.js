const actionContainer = document.getElementById("actionContainer");
const ticketSelectContainer = document.getElementById("ticketSelectContainer");
const ticketListContainer = document.getElementById("ticketListContainer");
const dashboardContainer = document.getElementById("dashboardContainer");

const addTicketTypeModal = document.getElementById("addTicketTypeModal");

const loadingSpinner = document.getElementById("loadingSpinner");

const pathParts = window.location.pathname.split('/').filter(Boolean);
const guildId = pathParts[pathParts.length - 1];

const maxTickets = document.getElementById("maxTickets");
const ticketName = document.getElementById("ticketName");
const roleListDropdown = document.getElementById("roleListDropdown");
const surveyCheck1 = document.getElementById("surveyCheck1");
const surveyCheck2 = document.getElementById("surveyCheck2");
const surveyCheck3 = document.getElementById("surveyCheck3");
const survey1Input = document.getElementById("survey1Input");
const survey2Input = document.getElementById("survey2Input");
const survey3Input = document.getElementById("survey3Input");

containerList = [actionContainer, ticketListContainer, ticketSelectContainer];

document.querySelectorAll(".previousButton").forEach(button => {
    button.addEventListener("click", () => {
        containerList.forEach(element => {
            element.classList.add("d-none");
        });
        actionContainer.classList.remove("d-none");
    });
});
document.getElementById("ticketSettingButton").addEventListener("click", async () => {
    actionContainer.classList.add("d-none");
    list = await fetchTicketTypeList();
    renderTicketTypeList(list);
    ticketSelectContainer.classList.remove("d-none");
});

document.getElementById("ticketListButton").addEventListener("click", async () => {
    actionContainer.classList.add("d-none");
    ticketListContainer.classList.remove("d-none");
});

function showSpinner() {
    loadingSpinner.classList.add("d-flex")
    loadingSpinner.classList.remove("d-none")
}

function hideSpinner() {
    loadingSpinner.classList.remove("d-flex");
    loadingSpinner.classList.add("d-none");
}

async function fetchTicketTypeList() {
    showSpinner();
    try {
        const res = await fetch(`/api/guilds/${guildId}/ticket-settings`);
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.error || "불러오기 실패");
        }

        return data.data;
    } catch (error) {
        alert(error.message);
    } finally {
        hideSpinner();
    }
}

function renderTicketTypeList(ticketTypeListArray) {
    const ticketTypeList = document.getElementById("ticketTypeList");
    ticketTypeList.innerHTML = "";
    ticketTypeListArray.forEach((ticketType, index) => {
        const option = document.createElement("option");
        option.value = index;
        option.textContent = ticketType.name;
        ticketTypeList.appendChild(option);
    });
}

async function fetchTicketList(query = "") {
    showSpinner();
    try {
        let url = `/api/tickets/ticketlist?guild_id=${guildId}`;
        if (query) {
            url += `&query=${encodeURIComponent(query)}`;
        }
        const response = await fetch(url);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "불러오기 실패");
        }
        return Array.isArray(data) ? data : data.tickets || [];
    } catch (error) {
        alert(error.message);
        return [];
    } finally {
        hideSpinner();
    }
}

function renderTickets(tickets) {
    const ticketsPerPage = 10;
    const totalPages = Math.ceil(tickets.length / ticketsPerPage);
    const start = (currentPage - 1) * ticketsPerPage;
    const end = start + ticketsPerPage;
    const pageTickets = tickets.slice(start, end);

    if (tickets.length === 0) {
        ticketListBody.innerHTML = `<tr><td colspan="3">검색 결과가 없습니다.</td></tr>`;
        renderPagination(0, 0);
        return;
    }

    ticketListBody.innerHTML = pageTickets.map(ticket => `
        <tr>
            <td>${ticket.username}</td>
            <td>${ticket.datetime}</td>
            <td>
                <a href="/tickets/${guildId}/${ticket.path}" target="_blank">
                    <button class="btn btn-sm btn-outline-primary">보기</button>
                </a>
            </td>
        </tr>
    `).join("");

    renderPagination(currentPage, totalPages);
}

function renderPagination(current, totalPages) {
    if (totalPages === 0) {
        pagination.innerHTML = "";
        return;
    }

    let html = `
        <li class="page-item ${current === 1 ? "disabled" : ""}">
            <button class="page-link" data-page="${current - 1}" aria-label="이전 페이지">
                <span aria-hidden="true">◀</span>
            </button>
        </li>`;

    for (let i = 1; i <= totalPages; i++) {
        html += `
            <li class="page-item ${i === current ? "active" : ""}" aria-current="${i === current ? "page" : undefined}">
                <button class="page-link" data-page="${i}">${i}</button>
            </li>`;
    }

    html += `
        <li class="page-item ${current === totalPages ? "disabled" : ""}">
            <button class="page-link" data-page="${current + 1}" aria-label="다음 페이지">
                <span aria-hidden="true">▶</span>
            </button>
        </li>`;

    pagination.innerHTML = html;

    pagination.querySelectorAll("button").forEach(btn => {
        if (!btn.parentElement.classList.contains("disabled")) {
            btn.addEventListener("click", () => {
                currentPage = Number(btn.dataset.page);
                renderTickets(currentTickets);
                window.scrollTo({ top: 0, behavior: "smooth" });
            });
        }
    });
}

addTicketTypeModal.addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = document.getElementById("inputAddTicketTypeName").value;
    try {
        const res = await fetch(`/api/guilds/${guildId}/ticket-settings`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                "name": name
            })
        });
        const data = await res.json();

        if (!res.ok) {
            Swal.fire({
                "title": "오류",
                "icon": "error",
                "text": data.error || "알 수 없는 오류입니다!",
                "confirmButtonText": "닫기"
            });
            return;
        }
        
        showSpinner();
        list = await fetchTicketTypeList();
        renderTicketTypeList(list);
        Swal.fire({
            "title": "티켓 종류 추가가 완료되었습니다!",
            "icon": "success",
            "confirmButtonText": "닫기"
        });
    } catch (error) {
        alert("오류");
        console.error(error);
    }
});

document.getElementById("ticketTypeSelect").addEventListener("change", async (e) => {
    showSpinner();

    try {
        const res = await fetch(`/api/guilds/${guildId}/roles`);
        const data = await res.json();
        roleListDropdown.innerHTML = "";

        if (res.ok) {
            data.data.forEach(role => {
                const div = document.createElement("div");
                div.className = "form-check";
                div.innerHTML = `
                <input class="form-check-input" type="checkbox" value="${role.id}" id="role-${role.id}">
                <label class="form-check-label" for="role-${role.id}">${role.name}</label>
                `;
                roleListDropdown.appendChild(div);
            });
        } else {
            roleListDropdown.innerHTML = `<option value='' selected disabled>${data.error}</option>`;
        }
    } catch (error) {
        Swal.fire({
            "title": "오류",
            "icon": "error",
            "text": error || "알 수 없는 오류입니다!",
            "confirmButtonText": "닫기"
        });
        return;
    }

    try {
        const res = await fetch(`/api/guilds/${guildId}/ticket-settings/${e.target.value}`);
        const data = await res.json();

        if (!res.ok) {
            Swal.fire({
                "title": "오류",
                "icon": "error",
                "text": error || "알 수 없는 오류입니다!",
                "confirmButtonText": "닫기"
            });
            return;
        }

        ticketName.value = data.data.name;
        maxTickets.value = data.data.max_ticket;

        surveyCheck1.checked = Boolean(data.data.survey1);
        surveyCheck2.checked = Boolean(data.data.survey2);
        surveyCheck3.checked = Boolean(data.data.survey3);

        survey1Input.value = data.data.survey1;
        survey2Input.value = data.data.survey2;
        survey3Input.value = data.data.survey3;

        for (let role of data.data.role) {
            const checkbox = document.getElementById(`role-${role}`);
            if (checkbox) {
                checkbox.checked = true;
            }
        }
    } catch (error) {
        console.error(error);
        Swal.fire({
            "title": "오류",
            "icon": "error",
            "text": error || "알 수 없는 오류입니다!",
            "confirmButtonText": "닫기"
        });
        return;
    }

    hideSpinner();
    ticketSelectContainer.classList.add("d-none");
    dashboardContainer.classList.remove("d-none");
})