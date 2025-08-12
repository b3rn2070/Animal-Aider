// ========================================
// FUNÇÕES DE VALIDAÇÃO NUMÉRICA
// ========================================

/**
 * Permite apenas números em um campo de input
 * @param {HTMLElement} input - O elemento input
 */
function allowOnlyNumbers(input) {
    input.addEventListener('input', function(e) {
        // Remove tudo que não for número
        this.value = this.value.replace(/\D/g, '');
    });
    
    // Previne colar texto não numérico
    input.addEventListener('paste', function(e) {
        e.preventDefault();
        let pastedData = (e.clipboardData || window.clipboardData).getData('text');
        // Remove caracteres não numéricos do texto colado
        this.value = pastedData.replace(/\D/g, '');
    });
    
    // Previne digitação de caracteres não numéricos
    input.addEventListener('keypress', function(e) {
        // Permite apenas números (0-9), backspace, delete, tab, enter, e setas
        const allowedKeys = [8, 9, 13, 46, 37, 38, 39, 40];
        const isNumber = (e.charCode >= 48 && e.charCode <= 57);
        
        if (!isNumber && allowedKeys.indexOf(e.keyCode) === -1) {
            e.preventDefault();
        }
    });
}

/**
 * Aplica máscara de telefone enquanto digita
 * Formato: (11) 99999-9999
 */
function applyPhoneMask(input) {
    input.addEventListener('input', function(e) {
        let value = this.value.replace(/\D/g, ''); // Remove não números
        
        if (value.length <= 11) {
            // Aplica máscara baseada no tamanho
            if (value.length <= 2) {
                value = value.replace(/(\d{0,2})/, '($1');
            } else if (value.length <= 6) {
                value = value.replace(/(\d{2})(\d{0,4})/, '($1) $2');
            } else if (value.length <= 10) {
                value = value.replace(/(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3');
            } else {
                value = value.replace(/(\d{2})(\d{5})(\d{0,4})/, '($1) $2-$3');
            }
            
            this.value = value;
        } else {
            // Limita a 11 dígitos
            this.value = this.value.slice(0, 14); // Considera os caracteres da máscara
        }
    });
}

/**
 * Aplica máscara de CEP enquanto digita
 * Formato: 12345-678
 */
function applyCepMask(input) {
    input.addEventListener('input', function(e) {
        let value = this.value.replace(/\D/g, ''); // Remove não números
        
        if (value.length <= 8) {
            if (value.length > 5) {
                value = value.replace(/(\d{5})(\d{0,3})/, '$1-$2');
            }
            this.value = value;
        } else {
            // Limita a 8 dígitos
            this.value = this.value.slice(0, 9); // Considera o hífen
        }
    });
}

/**
 * Aplica máscara de CPF enquanto digita
 * Formato: 123.456.789-10
 */
function applyCpfMask(input) {
    input.addEventListener('input', function(e) {
        let value = this.value.replace(/\D/g, ''); // Remove não números
        
        if (value.length <= 11) {
            if (value.length <= 3) {
                // Primeiros 3 dígitos
                value = value.replace(/(\d{0,3})/, '$1');
            } else if (value.length <= 6) {
                // Até 6 dígitos: 123.456
                value = value.replace(/(\d{3})(\d{0,3})/, '$1.$2');
            } else if (value.length <= 9) {
                // Até 9 dígitos: 123.456.789
                value = value.replace(/(\d{3})(\d{3})(\d{0,3})/, '$1.$2.$3');
            } else {
                // CPF completo: 123.456.789-10
                value = value.replace(/(\d{3})(\d{3})(\d{3})(\d{0,2})/, '$1.$2.$3-$4');
            }
            
            this.value = value;
        } else {
            // Limita a 11 dígitos
            this.value = this.value.slice(0, 14); // Considera os caracteres da máscara (3 pontos + 1 hífen)
        }
    });
}

/**
 * Permite apenas números no campo CPF (sem máscara)
 * @param {HTMLElement} input - O elemento input do CPF
 */
function allowOnlyNumbersCpf(input) {
    input.addEventListener('input', function(e) {
        // Remove tudo que não for número e limita a 11 dígitos
        let value = this.value.replace(/\D/g, '');
        if (value.length > 11) {
            value = value.slice(0, 11);
        }
        this.value = value;
    });
    
    // Previne colar texto não numérico
    input.addEventListener('paste', function(e) {
        e.preventDefault();
        let pastedData = (e.clipboardData || window.clipboardData).getData('text');
        // Remove caracteres não numéricos do texto colado e limita a 11 dígitos
        let cleanData = pastedData.replace(/\D/g, '');
        if (cleanData.length > 11) {
            cleanData = cleanData.slice(0, 11);
        }
        this.value = cleanData;
    });
    
    // Previne digitação de caracteres não numéricos
    input.addEventListener('keypress', function(e) {
        // Permite apenas números (0-9), backspace, delete, tab, enter, e setas
        const allowedKeys = [8, 9, 13, 46, 37, 38, 39, 40];
        const isNumber = (e.charCode >= 48 && e.charCode <= 57);
        
        // Também verifica se já chegou ao limite de 11 dígitos
        const currentNumbers = this.value.replace(/\D/g, '');
        if (currentNumbers.length >= 11 && isNumber) {
            e.preventDefault();
            return;
        }
        
        if (!isNumber && allowedKeys.indexOf(e.keyCode) === -1) {
            e.preventDefault();
        }
    });
}

/**
 * Valida se o campo contém apenas números
 * @param {HTMLElement} input - O elemento input
 * @returns {boolean} - true se válido, false se inválido
 */
function validateNumericField(input) {
    const value = input.value.replace(/\D/g, ''); // Remove não números para validação
    const isValid = value.length > 0;
    
    // Aplica estilo visual de erro
    if (isValid) {
        input.classList.remove('error');
        input.classList.add('valid');
    } else {
        input.classList.add('error');
        input.classList.remove('valid');
    }
    
    return isValid;
}

/**
 * Valida telefone (deve ter 10 ou 11 dígitos)
 * @param {HTMLElement} input - O elemento input do telefone
 * @returns {boolean} - true se válido
 */
function validatePhone(input) {
    const numbers = input.value.replace(/\D/g, '');
    const isValid = numbers.length >= 10 && numbers.length <= 11;
    
    if (isValid) {
        input.classList.remove('error');
        input.classList.add('valid');
        hideErrorMessage(input);
    } else {
        input.classList.add('error');
        input.classList.remove('valid');
        showErrorMessage(input, 'Telefone deve ter 10 ou 11 dígitos');
    }
    
    return isValid;
}

/**
 * Valida CEP (deve ter 8 dígitos)
 * @param {HTMLElement} input - O elemento input do CEP
 * @returns {boolean} - true se válido
 */
function validateCep(input) {
    const numbers = input.value.replace(/\D/g, '');
    const isValid = numbers.length === 8;
    
    if (isValid) {
        input.classList.remove('error');
        input.classList.add('valid');
        hideErrorMessage(input);
    } else {
        input.classList.add('error');
        input.classList.remove('valid');
        showErrorMessage(input, 'CEP deve ter 8 dígitos');
    }
    
    return isValid;
}

/**
 * Valida CPF (deve ter 11 dígitos)
 * @param {HTMLElement} input - O elemento input do CPF
 * @returns {boolean} - true se válido
 */
function validateCpf(input) {
    const numbers = input.value.replace(/\D/g, '');
    const isValid = numbers.length === 11;
    
    if (isValid) {
        input.classList.remove('error');
        input.classList.add('valid');
        hideErrorMessage(input);
    } else {
        input.classList.add('error');
        input.classList.remove('valid');
        showErrorMessage(input, 'CPF deve ter 11 dígitos');
    }
    
    return isValid;
}

/**
 * Mostra mensagem de erro abaixo do campo
 */
function showErrorMessage(input, message) {
    hideErrorMessage(input); // Remove mensagem anterior
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    errorDiv.style.color = 'red';
    errorDiv.style.fontSize = '12px';
    errorDiv.style.marginTop = '5px';
    
    input.parentNode.appendChild(errorDiv);
}

/**
 * Remove mensagem de erro
 */
function hideErrorMessage(input) {
    const errorMessage = input.parentNode.querySelector('.error-message');
    if (errorMessage) {
        errorMessage.remove();
    }
}

/**
 * Valida todos os campos numéricos do formulário
 * @param {HTMLFormElement} form - O formulário a ser validado
 * @returns {boolean} - true se todos os campos são válidos
 */
function validateNumericForm(form) {
    let isValid = true;
    
    // Valida telefone
    const phoneInput = form.querySelector('input[name="phone"]');
    if (phoneInput && !validatePhone(phoneInput)) {
        isValid = false;
    }
    
    // Valida CEP
    const cepInput = form.querySelector('input[name="cep"]');
    if (cepInput && !validateCep(cepInput)) {
        isValid = false;
    }
    
    // Valida CPF
    const cpfInput = form.querySelector('input[name="cpf"]');
    if (cpfInput && !validateCpf(cpfInput)) {
        isValid = false;
    }
    
    // Valida campo número (deve ter pelo menos 1 dígito)
    const numInput = form.querySelector('input[name="num"]');
    if (numInput) {
        const numbers = numInput.value.replace(/\D/g, '');
        if (numbers.length === 0) {
            numInput.classList.add('error');
            showErrorMessage(numInput, 'Campo obrigatório - apenas números');
            isValid = false;
        } else {
            numInput.classList.remove('error');
            numInput.classList.add('valid');
            hideErrorMessage(numInput);
        }
    }
    
    return isValid;
}

// ========================================
// INICIALIZAÇÃO AUTOMÁTICA
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    // Aplica validação nos campos quando a página carrega
    
    // Campo telefone
    const phoneInput = document.querySelector('input[name="phone"]');
    if (phoneInput) {
        applyPhoneMask(phoneInput);
        phoneInput.addEventListener('blur', () => validatePhone(phoneInput));
    }
    
    // Campo CEP  
    const cepInput = document.querySelector('input[name="cep"]');
    if (cepInput) {
        applyCepMask(cepInput);
        cepInput.addEventListener('blur', () => validateCep(cepInput));
    }
    
    // Campo CPF
    const cpfInput = document.querySelector('input[name="cpf"]');
    if (cpfInput) {
        // Você pode escolher entre máscara ou apenas números:
        // Para máscara: applyCpfMask(cpfInput);
        // Para apenas números: allowOnlyNumbersCpf(cpfInput);
        
        allowOnlyNumbersCpf(cpfInput); // Aplicando apenas números
        cpfInput.addEventListener('blur', () => validateCpf(cpfInput));
    }
    
    // Campo número
    const numInput = document.querySelector('input[name="num"]');
    if (numInput) {
        allowOnlyNumbers(numInput);
        numInput.addEventListener('blur', () => validateNumericField(numInput));
    }
    
    // Validação no envio do formulário
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validateNumericForm(this)) {
                e.preventDefault();
                alert('Por favor, corrija os erros nos campos destacados.');
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const cepInput = document.getElementById('cep');
    const addrInput = document.getElementById('addr');
    const citySelect = document.getElementById('city'); // Assumindo que é um select
    
    // Verifica se os elementos existem
    if (!cepInput) return;
    
    // Função para limpar campos
    function clearAddressFields() {
        if (addrInput) addrInput.value = '';
        if (citySelect) citySelect.value = '';
    }
    
    // Função para mostrar loading
    function showLoading(show = true) {
        if (addrInput) {
            addrInput.style.backgroundColor = show ? '#f0f0f0' : '';
            addrInput.placeholder = show ? 'Buscando endereço...' : '';
            addrInput.disabled = show;
        }
    }
    
    // Função principal de busca CEP
    function searchCEP(cep) {
        // Limpa campos antes de buscar
        clearAddressFields();
        showLoading(true);
        
        fetch(`/get_address/${cep}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                showLoading(false);
                
                if (!data.erro) {
                    // Preenche endereço
                    if (addrInput && data.logradouro) {
                        addrInput.value = data.logradouro;
                    }
                    
                    // Preenche cidade (tratamento para select)
                    if (citySelect && data.localidade) {
                        // Se for um select, tenta encontrar a opção
                        if (citySelect.tagName.toLowerCase() === 'select') {
                            const options = Array.from(citySelect.options);
                            const cityOption = options.find(option => 
                                option.value === data.localidade || 
                                option.text === data.localidade
                            );
                            
                            if (cityOption) {
                                citySelect.value = cityOption.value;
                            } else {
                                console.warn(`Cidade "${data.localidade}" não encontrada no select`);
                            }
                        } else {
                            // Se for input normal
                            citySelect.value = data.localidade;
                        }
                    }
                    
                    // Feedback visual de sucesso
                    cepInput.style.borderColor = '#4CAF50';
                    setTimeout(() => {
                        cepInput.style.borderColor = '';
                    }, 2000);
                    
                } else {
                    // CEP não encontrado
                    showCepError('CEP não encontrado. Verifique se todos os 8 dígitos estão corretos.');
                }
            })
            .catch(error => {
                showLoading(false);
                console.error('Erro ao buscar CEP:', error);
                showCepError('Erro ao buscar o endereço. Tente novamente.');
            });
    }
    
    // Função para mostrar erros
    function showCepError(message) {
        cepInput.style.borderColor = '#ff4444';
        
        // Remove mensagem de erro anterior
        const existingError = cepInput.parentNode.querySelector('.cep-error');
        if (existingError) {
            existingError.remove();
        }
        
        // Cria nova mensagem de erro
        const errorDiv = document.createElement('div');
        errorDiv.className = 'cep-error';
        errorDiv.textContent = message;
        errorDiv.style.cssText = `
            color: #ff4444;
            font-size: 12px;
            margin-top: 5px;
            display: block;
        `;
        
        cepInput.parentNode.appendChild(errorDiv);
        
        // Remove erro após 5 segundos
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
                cepInput.style.borderColor = '';
            }
        }, 5000);
    }
    
    // Event listener para busca automática
    cepInput.addEventListener('blur', function() {
        const cep = this.value.replace(/\D/g, '');
        
        // Remove mensagens de erro anteriores
        const existingError = this.parentNode.querySelector('.cep-error');
        if (existingError) {
            existingError.remove();
        }
        
        if (cep.length === 8) {
            searchCEP(cep);
        } else if (cep.length > 0) {
            showCepError(`CEP deve ter 8 dígitos (digitados: ${cep.length}/8).`);
            clearAddressFields();
        }
    });
    
    // Validação em tempo real - busca automática quando completar 8 dígitos
    let searchTimeout;
    cepInput.addEventListener('input', function() {
        const cep = this.value.replace(/\D/g, '');
        
        // Remove mensagens de erro anteriores se estiver digitando
        const existingError = this.parentNode.querySelector('.cep-error');
        if (existingError) {
            existingError.remove();
        }
        
        clearTimeout(searchTimeout);
        
        if (cep.length === 8) {
            // Busca automaticamente quando completar 8 dígitos
            searchTimeout = setTimeout(() => {
                searchCEP(cep);
            }, 800); // Aguarda 800ms após completar os 8 dígitos
        } else if (cep.length > 8) {
            // Não deveria acontecer, mas garante que não passe de 8
            this.value = cep.substring(0, 8);
        } else {
            // Limpa campos se CEP incompleto
            clearAddressFields();
        }
    });
});

function previewImage(event) {
    const file = event.target.files[0];
    const reader = new FileReader();
    
    reader.onload = function(e) {
        // Atualiza a imagem no navegador com a nova imagem
        document.getElementById('photo').src = e.target.result;
    };
    
    if (file) {
        reader.readAsDataURL(file); // Lê o arquivo como URL de dados
    }
}