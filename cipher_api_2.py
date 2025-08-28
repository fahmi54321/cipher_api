# --------------------------------------------------------------------------------------
# PERTAMA, kita melakukan import library yang dibutuhkan:
# 1. numpy → untuk operasi numerik.
# 2. string → menyediakan cara mudah memuat semua karakter ASCII valid (misalnya huruf a-z).
# 3. random → untuk mengacak huruf ASCII, sehingga kita bisa membuat substitution cipher.
# 4. re (regex) → untuk operasi teks (misalnya pencarian pola string).
# 5. os dan textwrap → untuk beberapa tugas tambahan di bagian lain dari skrip.
# 6. requests → untuk mengunduh teks dari internet (misalnya Project Gutenberg).
# --------------------------------------------------------------------------------------


import numpy as np
import string
import random
import re
import requests
import os
import textwrap
from flask import Flask, request, jsonify

app = Flask(__name__)

# --------------------------------------------
# MEMBUAT dua list berisi huruf-huruf alfabet:
# --------------------------------------------
letters1 = list(string.ascii_lowercase)
letters2 = list(string.ascii_lowercase)

# ----------------------------------------------------------------
# MEMBUAT dictionary kosong untuk mapping huruf asli ke huruf acak:
# ----------------------------------------------------------------
true_mapping = {}

# ----------------------------------------------------------------
# MENGACAK list huruf kedua (letters2):
# Sedangkan letters1 tetap berisi huruf alfabet berurutan.
# 1. letters1 → sebagai key dictionary (huruf asli).
# 2. letters2 → sebagai value dictionary (huruf hasil enkripsi).
# ----------------------------------------------------------------
random.shuffle(letters2)

# ----------------------------------------------------------------------------------------------------------------------
# SELANJUTNYA, kita melakukan looping (perulangan) melalui kedua list (letters1 dan letters2) secara berpasangan.
# 1. Pada iterasi pertama, k akan berisi elemen pertama dari letters1, dan v akan berisi elemen pertama dari letters2.
# 2. Pada iterasi kedua, k akan berisi elemen kedua dari letters1, dan v akan berisi elemen kedua dari letters2.
# 3. Dan seterusnya, sampai semua huruf habis.
# Di dalam loop ini, kita menetapkan k sebagai key (kunci) pada dictionary true_mapping, dan v sebagai value (nilai)-nya.
# ----------------------------------------------------------------------------------------------------------------------
for k, v in zip(letters1, letters2):
  true_mapping[k] = v


# ----------------------------------------------------------------------------------------------------
# MATRIKS ini digunakan untuk menyimpan semua probabilitas bigram (peluang kemunculan pasangan huruf).
# ----------------------------------------------------------------------------------------------------
M = np.ones((26, 26))
M

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
# KITA juga memerlukan sebuah vektor untuk menyimpan probabilitas unigram, lebih spesifiknya untuk merepresentasikan distribusi keadaan awal (initial state distribution).
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
pi = np.zeros(26)
pi

# -------------------------------------------------------------------------
# FUNGSI untuk memperbarui matriks M
# -------------------------------------------------------------------------
def update_transition(ch1, ch2):
  # ord('a') = 97, ord('b') = 98, ...
  i = ord(ch1) - 97
  j = ord(ch2) - 97
  M[i,j] += 1

# -------------------------------------------------------------------------
# FUNGSI untuk memperbarui π (pi)
# -------------------------------------------------------------------------
def update_pi(ch):
  i = ord(ch) - 97
  pi[i] += 1

# ------------------------------------------------------------------------------------------------------------------------
# FUNGSI berikut digunakan untuk menghitung log probability (probabilitas dalam bentuk logaritma) dari sebuah kata tunggal.
# ------------------------------------------------------------------------------------------------------------------------
def get_word_prob(word):
  # print("word:", word)
  i = ord(word[0]) - 97
  logp = np.log(pi[i])

  for ch in word[1:]:
    j = ord(ch) - 97
    logp += np.log(M[i, j]) # update prob
    i = j # update j

  return logp

# ----------------------------------------------------------------------------------
# FUNGSI yang mengembalikan log probability dari keseluruhan urutan kata (sequence).
# ----------------------------------------------------------------------------------
def get_sequence_prob(words):
  # if input is a string, split into an array of tokens
  if type(words) == str:
    words = words.split()

  logp = 0
  for word in words:
    logp += get_word_prob(word)
  return logp

# ---------------
# MENGUNDUH data.
# ---------------
if not os.path.exists('moby_dick.txt'):
  print("Downloading moby dick...")
  r = requests.get('https://raw.githubusercontent.com/fahmi54321/cipher_api/refs/heads/main/moby_dick.txt')
  with open('moby_dick.txt', 'w') as f:
    f.write(r.content.decode())
    
# -----------------------------------
# MEMBUAT regex untuk filter karakter
# -----------------------------------
regex = re.compile('[^a-zA-Z]')
regex

# ---------------------------------------
# Membaca file Moby Dick baris demi baris
# ---------------------------------------
for line in open('moby_dick.txt'):
  line = line.rstrip()

  # there are blank lines in the file
  if line:
    line = regex.sub(' ', line) # replace all non-alpha characters with space

    # split the tokens in the line and lowercase
    tokens = line.lower().split()

    for token in tokens:
      # update the model

      # first letter
      ch0 = token[0]
      update_pi(ch0)

      # other letters
      for ch1 in token[1:]:
        update_transition(ch0, ch1)
        ch0 = ch1

# ---------------------------
# NORMALIZE the probabilities
# ---------------------------
pi /= pi.sum()
pi
M /= M.sum(axis=1, keepdims=True)
M

original_message = '''I then lounged down the street and found,
as I expected, that there was a mews in a lane which runs down
by one wall of the garden. I lent the ostlers a hand in rubbing
down their horses, and received in exchange twopence, a glass of
half-and-half, two fills of shag tobacco, and as much information
as I could desire about Miss Adler, to say nothing of half a dozen
other people in the neighbourhood in whom I was not in the least
interested, but whose biographies I was compelled to listen to.
'''

# ------------------------------
# FUNGSI untuk meng-encode pesan
# ------------------------------
def encode_message(msg):
  # downcase
  msg = msg.lower()

  # replace non-alpha characters
  msg = regex.sub(' ', msg)

  # make the encoded message
  coded_msg = []
  for ch in msg:
    coded_ch = ch # could just be a space
    if ch in true_mapping:
      coded_ch = true_mapping[ch]
    coded_msg.append(coded_ch)

  return ''.join(coded_msg)

encoded_message = encode_message(original_message)


# ------------------------------
# FUNGSI untuk meng-decode pesan
# ------------------------------
def decode_message(msg, word_map):
  decoded_msg = []
  for ch in msg:
    decoded_ch = ch # could just be a space
    if ch in word_map:
      decoded_ch = word_map[ch]
    decoded_msg.append(decoded_ch)

  return ''.join(decoded_msg)


# --------------------------------------------------------------------------------------
# UNTUK memulai algoritma, kita perlu membuat sebuah DNA pool yang berisi 20 DNA string.
# --------------------------------------------------------------------------------------
dna_pool = []
for _ in range(20):
  dna = list(string.ascii_lowercase)
  random.shuffle(dna)
  dna_pool.append(dna)

# ------------------------------------------------
# FUNGSI untuk mengembangkan keturunan (offspring)
# ------------------------------------------------
def evolve_offspring(dna_pool, n_children):
  # make n_children per offspring
  offspring = []

  for dna in dna_pool:
    for _ in range(n_children):
      copy = dna.copy()
      j = np.random.randint(len(copy))
      k = np.random.randint(len(copy))

      # switch
      tmp = copy[j]
      copy[j] = copy[k]
      copy[k] = tmp
      offspring.append(copy)

  return offspring + dna_pool

# -------------------------------------------------------------------------------------
# SELANJUTNYA, kita masuk ke loop utama yang benar-benar menjalankan algoritma genetika.
# -------------------------------------------------------------------------------------
num_iters = 1000
scores = np.zeros(num_iters)
best_dna = None
best_map = None
best_score = float('-inf')
for i in range(num_iters):
  if i > 0:
    # get offspring from the current dna pool
    dna_pool = evolve_offspring(dna_pool, 3)

  # calculate score for each dna
  dna2score = {}
  for dna in dna_pool:
    # populate map
    current_map = {}
    for k, v in zip(letters1, dna):
      current_map[k] = v

    decoded_message = decode_message(encoded_message, current_map)
    score = get_sequence_prob(decoded_message)

    # store it
    # needs to be a string to be a dict key
    dna2score[''.join(dna)] = score

    # record the best so far
    if score > best_score:
      best_dna = dna
      best_map = current_map
      best_score = score

  # average score for this generation
  scores[i] = np.mean(list(dna2score.values()))

  # keep the best 5 dna
  # also turn them back into list of single chars
  sorted_dna = sorted(dna2score.items(), key=lambda x: x[1], reverse=True)
  dna_pool = [list(k) for k, v in sorted_dna[:5]]

# -------------------------------------------------------------------------------------
# LALU, kita ingin mengecek seberapa bagus hasil decoding itu. 
# Caranya adalah dengan menghitung log likelihood (LL) dari pesan hasil decode dibandingkan 
# dengan log likelihood dari pesan asli yang benar.
# -------------------------------------------------------------------------------------
decoded_message = decode_message(encoded_message, best_map)
print("LL of decoded message:", get_sequence_prob(decoded_message))
print("LL of true message:", get_sequence_prob(regex.sub(' ', original_message.lower())))


# -----------------------------------------------------------------------
# Berikutnya, kita ingin tahu huruf mana saja yang diprediksi salah. 
# Maka dilakukan looping terhadap true_mapping (mapping asli yang benar).
# -----------------------------------------------------------------------
for true, v in true_mapping.items():
  pred = best_map[v]
  if true != pred:
    print("true: %s, pred: %s" % (true, pred))

# ----------------------------------------------------------------
# Akhirnya kita cetak isi pesan hasil decode dengan isi pesan asli
# ----------------------------------------------------------------
print("Decoded message:\n", textwrap.fill(decoded_message))

print("\nTrue message:\n", original_message)

# -------------------------
# FLASK ROUTES
# -------------------------

@app.route("/encode", methods=["POST"])
def encode_api():
    data = request.json
    text = data.get("text", "")
    encoded = encode_message(text)
    return jsonify({"encoded": encoded})

@app.route("/decode", methods=["POST"])
def decode_api():
    data = request.json
    encoded = data.get("text", "")
    decoded = decode_message(encoded, best_map)
    return jsonify({"decoded": decoded})

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)












    