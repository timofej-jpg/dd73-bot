let tg = window.Telegram.WebApp;
tg.expand();

document.getElementById("sendBtn").addEventListener("click", () => {
    let fish = document.getElementById("fish").value;
    let weight = document.getElementById("weight").value;

    if (!weight) {
        tg.showAlert("Пожалуйста, введи вес рыбы!");
        return;
    }

    let data = {
        fish: fish,
        weight: weight
    };

    tg.sendData(JSON.stringify(data));
});
