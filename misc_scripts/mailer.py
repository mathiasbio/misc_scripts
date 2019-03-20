#!/apps/bio/software/anaconda2/envs/sentieon_py/bin/python

def send_mail(subj, body, bifogad_fil, recipients=[], sender='clinicalgenomics@gu.se'):
    from marrow.mailer import Mailer, Message
    """Send mail to specified recipients."""
    recipients = ['mathias.johansson@gu.se', *recipients]
    mailer = Mailer(dict(
        transport=dict(use='smtp',
                       host='smtp.gu.se')))

    mailer.start()
    message = Message(
        subject=f'{subj}',
        plain=f'{body}',
        author=sender,
        to=recipients,)
    message.attach(str(bifogad_fil))
    mailer.send(message)
    mailer.stop()

