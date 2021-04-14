from flask import Flask
import optimizer
app = Flask(__name__)

@app.route('/optimize')
def optimize():
    result = optimizer.optimize()
    return result

if __name__ == '__main__':
    app.run()