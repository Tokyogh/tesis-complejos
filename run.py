from app import create_app

app = create_app()

if __name__ == "__main__":
    print("=" * 62)
    print(" SISTEMA DE ESTIMACIÓN DE POLIDEPORTIVOS")
    print(" Servidor disponible en http://127.0.0.1:5000")
    print("=" * 62)
    app.run(debug=True)