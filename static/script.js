async function getCoin() {
    const coin = document.getElementById("coin").value;
    const currency = document.getElementById("currency").value;
    const days = document.getElementById("days").value;

    const res = await fetch("/api/coin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ coin, currency, days })
    });

    const data = await res.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    document.getElementById("price").textContent = ${coin.toUpperCase()} Fiyatı: ${data.price} ${currency.toUpperCase()};
    document.getElementById("logo").src = data.logo_url;

    const ctx = document.getElementById("chart").getContext("2d");
    new Chart(ctx, {
        type: "line",
        data: {
            labels: data.labels,
            datasets: [{
                label: "Fiyat",
                data: data.data,
                borderColor: "blue",
                backgroundColor: "lightblue",
                fill: true,
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: { ticks: { color: "black" } },
                y: { ticks: { color: "black" } }
            }
        }
    });
}