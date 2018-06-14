# Trabalho 2 de Formais


## I – Definição:

Elaborar uma aplicação,
com interface gráfica para manipular GLC,
envolvendo as seguintes verificações/operações:
1. Editar textualmente GLC’s;
2. Verificar se L(G) é vazia, finita ou infinita;
3. Transformar uma GLC em GLC Própria,
   disponibilizando: Gramáticas intermediárias, NF, Vi, Ne e NA;
4. Calcular First(A),
   Follow(A) e First-NT(A) (definido como sendo o conjunto de símbolos de Vn que podem iniciar sequências derivadas de A) para todo A ∈ Vn;
5. Verificar se G está fatorada ou se é fatorável em n passos;
6. Verificar se G possui ou não Rec.
   a Esquerda – identificando os não-terminais recursivos a esquerda e o tipo das recursões (direta e/ou indireta) e, caso possua,
   eliminar as recursões.


## II - Observações:
1. Representar as GLC de forma textual, seguindo o padrão dos exemplos abaixo:
    ### a)
    ```
    E -> E + T | E - T | T
    T -> T * F | T / F | F
    F -> ( E ) | id
    ```

    ### b)
    ```
     E -> T E1
    E1 -> + T E1 | &
     T -> F T1
    T1 -> * F T1 | &
     F -> ( E ) | id
    ```
2. deixar um espaço em branco entre os símbolos do lado direito.
3. Representar não-terminais por letra maiúscula (seguida de 0 ou + dígitos).
4. Representar terminais com um ou mais caracteres contíguos (quaisquer caracteres,
   exceto letras maiúsculas).
5. Usar & para representar épsilon.
6. Apresentar os resultados intermediários obtidos.
7. O trabalho deverá ser feito em duplas e a linguagem de programação é de livre escolha (porém deve ser dominada pelos 2 membros da equipe).
8. O trabalho deve ser encaminhado por e-mail, até **27/06**,
   em um único arquivo zipado,
   contendo relatório (descrevendo a implementação), fonte (documentado),
   executável e testes.
   Usar como nome do arquivo o nome dos componentes da equipe (ex.
   JoaoF-MariaG.zip).
   9 – Além da corretude,
   serão avaliados aspectos de usabilidade e robustez da aplicação.
