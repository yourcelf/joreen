ifdef vault_password_file
  VAULT = --vault-password-file $(vault_password_file)
else ifdef ANSIBLE_VAULT_PASSWORD_FILE_ITSOTO
  VAULT = --vault-password-file $(ANSIBLE_VAULT_PASSWORD_FILE_ITSOTO)
else
  VAULT = --ask-vault-pass
endif
ifdef tags
  TAGS = --tags $(tags)
endif
ifdef user
	USER = --user $(user)
else
	USER = --user tc1
endif
ifdef rootuser
	ROOT_USER = --user $(rootuser)
else
	ROOT_USER = --user root
endif

all:
	ansible-playbook -i hosts.cfg joreen.yml $(VAULT) $(TAGS) $(USER)

app:
	ansible-playbook -i hosts.cfg joreen.yml $(VAULT) --tags=django,joreen $(USER) 

code:
	ansible-playbook -i hosts.cfg joreen.yml $(VAULT) --tags=djangocode $(USER)

firstrun:
	ansible-playbook -i hosts.cfg firstrun.yml $(VAULT) $(ROOT_USER)
	ansible-playbook -i hosts.cfg joreen.yml $(VAULT) $(EXTRA) $(ROOT_USER)
