import win32com.client as win32


class EnviarCorreo:
    def __init__(self, fecha, getGlobalConfiguration):
        self.fecha = fecha
        self.getGlobalConfiguration = getGlobalConfiguration

    def estructura_correo(self, df_offus, df_onus, df_rechazadas, extra: str = ""):
        try:
            email = self.getGlobalConfiguration["email"]
            outlook = win32.Dispatch("outlook.application")
            mail = outlook.CreateItem(0)
            mail.To = email["to"]
            mail.CC = email["cc"]

            mail.Subject = f"Conciliación interoperabilidad {self.fecha}"

            mail.HTMLBody = f"""
                <html>
                <head></head>
                <body>
                <p>Cordial saludo,</p>
                <p>Se envia la información sobre la conciliación de interoperabilidad {self.fecha}.</p>
                <p>Cociliado OFFUS.</p>
                <p>{df_offus.to_html(index=False)}</p>
                <p>Cociliado ONUS.</p>
                <p>{df_onus.to_html(index=False)}</p>
                <p>Rechazadas sin fecha.</p>
                <p>{df_rechazadas.to_html(index=False)}</p>
                {extra}
                </body>
                </html>
                """

            # Enviar el correo
            mail.Send()
            print("Correo enviado exitosamente.")

        except Exception as e:
            print(f"Error al enviar el correo: {e}")

    def estructura_correo_pmd(self, df_resultado):
        try:
            email = self.getGlobalConfiguration()["email"]
            outlook = win32.Dispatch("outlook.application")
            mail = outlook.CreateItem(0)
            mail.To = email["to"]
            mail.CC = email["cc"]

            mail.Subject = f"Compensación interoperabilidad {self.fecha}"

            mail.HTMLBody = f"""
            <html>
            <head></head>
            <body>
            <p>Cordial saludo,</p>
            <p>Se envia la información sobre la compensacion de interoperabilidad {self.fecha}.</p>
            <p>COMPENSADO.</p>
            <p>{df_resultado.to_html(index=False)}</p>
            </body>
            </html>
            """

            # Enviar el correo
            mail.Send()
            print("Correo enviado exitosamente.")

        except Exception as e:
            print(f"Error al enviar el correo: {e}")
