// Reference fix for a database API that accepts '?' positional parameters.
function lookupUser(req, db) {
  const id = req.get('x-user-id');
  return db.query('SELECT name FROM users WHERE id = ?', [id]);
}

module.exports = { lookupUser };
