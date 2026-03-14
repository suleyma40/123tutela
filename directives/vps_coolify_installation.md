# Directiva: Instalación de Coolify en VPS

Esta directiva define el proceso para conectar a un VPS vía SSH e instalar Coolify utilizando el script oficial de instalación.

## Objetivo
Instalar Coolify de forma automatizada en un servidor remoto.

## Entradas
- `VPS_IP`: Dirección IP del servidor.
- `VPS_USER`: Usuario SSH (preferiblemente root o un usuario con privilegios sudo).
- `VPS_SSH_KEY_PATH`: (Opcional) Ruta al archivo de llave privada SSH.
- `VPS_PASSWORD`: (Opcional) Contraseña si no se usa llave SSH.

## Herramientas/Scripts
- `execution/install_coolify_remote.py`: Script de Python que maneja la conexión SSH y la ejecución del comando.

## Pasos
1. Validar que las credenciales estén presentes en el entorno o suministradas.
2. Comprobar conectividad SSH con el servidor.
3. Ejecutar el comando oficial de instalación de Coolify:
   ```bash
   curl -fsSL https://get.coollabs.io/coolify/install.sh | bash
   ```
4. Verificar que el servicio esté corriendo (puerto 8000 por defecto).
5. Retornar la URL del dashboard de Coolify.

## Casos Límite y Errores
- **Error de Conexión**: Reintentar o reportar fallo de credenciales.
- **Falta de Recursos**: Coolify requiere al menos 2 vCPUs y 2GB de RAM. El script debe intentar detectar esto antes de instalar.
- **Firewall Bloqueando**: Asegurarse de que los puertos 80, 443, y 8000 estén abiertos.

## Salida
- Confirmación de instalación.
- URL de acceso (`http://<VPS_IP>:8000`).
