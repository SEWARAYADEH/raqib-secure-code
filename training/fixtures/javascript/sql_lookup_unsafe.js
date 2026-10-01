// Trusted test fixture only: the input becomes part of SQL text.
function lookupUser(req, db) {
  const id = req.get('x-user-id');
  return db.query(`SELECT name FROM users WHERE id = ${id}`);
}

module.exports = { lookupUser };
