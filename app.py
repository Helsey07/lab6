from flask import Flask, jsonify, request, render_template
import requests
import time
import threading

app = Flask(__name__)

# Список доступных инстансов без "http://"
instances = [
    {'ip': '127.0.0.1', 'port': 5001, 'status': 'active'},
    {'ip': '127.0.0.1', 'port': 5002, 'status': 'active'},
    {'ip': '127.0.0.1', 'port': 5003, 'status': 'active'}
]

# Индекс текущего активного инстанса для Round Robin
round_robin_index = 0

def check_health():
    """Проверяет состояние всех инстансов каждую секунду."""
    while True:
        for instance in instances:
            try:
                response = requests.get(f"http://{instance['ip']}:{instance['port']}/health", timeout=3)
                if response.status_code == 200:
                    instance['status'] = 'active'
                else:
                    instance['status'] = 'inactive'
            except requests.exceptions.RequestException:
                instance['status'] = 'inactive'
        time.sleep(5)

# Запуск проверки состояния инстансов в отдельном потоке
threading.Thread(target=check_health, daemon=True).start()

@app.route('/health')
def health():
    return jsonify(instances)

@app.route('/process')
def process():
    global round_robin_index

    # Поиск следующего активного инстанса для Round Robin
    for _ in range(len(instances)):
        instance = instances[round_robin_index]
        if instance['status'] == 'active':
            response = requests.get(f"http://{instance['ip']}:{instance['port']}/process")
            round_robin_index = (round_robin_index + 1) % len(instances)
            return response.text

        round_robin_index = (round_robin_index + 1) % len(instances)

    return jsonify({"error": "No active instances available"}), 503

@app.route('/')
def home():
    """Отображает Web UI с формой добавления и удаления инстансов, а также с состоянием инстансов."""
    return render_template('index.html', instances=instances)

@app.route('/add_instance', methods=['POST'])
def add_instance():
    ip = request.form['ip']
    port = request.form['port']
    instances.append({'ip': ip, 'port': int(port), 'status': 'active'})
    return jsonify(instances)

@app.route('/remove_instance', methods=['POST'])
def remove_instance():
    index = int(request.form['index'])
    if 0 <= index < len(instances):
        instances.pop(index)
        return jsonify(instances)
    return jsonify({"error": "Invalid index"}), 400

if __name__ == '__main__':
    app.run(port=5003)
