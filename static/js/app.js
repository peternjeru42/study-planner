function csrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : "";
}

window.studyPlanner = {
    updateStatus(url, status) {
        return fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken(),
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: new URLSearchParams({ status }),
        }).then((response) => response.json());
    },
    generatePlan(url) {
        return fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken(),
                "X-Requested-With": "XMLHttpRequest",
            },
        }).then((response) => response.json());
    },
};
