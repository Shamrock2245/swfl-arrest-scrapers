import { test } from 'node:test';
import assert from 'node:assert';
import { normalizeRecord, parseFullName, normalizeMoney } from '../normalizers/normalize.js';

test('parseFullName - LAST, FIRST format', () => {
  const result = parseFullName('SMITH, JOHN MICHAEL');
  assert.strictEqual(result.first, 'John');
  assert.strictEqual(result.last, 'Smith');
  assert.strictEqual(result.lastFirst, 'Smith, John Michael');
});

test('parseFullName - FIRST LAST format', () => {
  const result = parseFullName('JOHN MICHAEL SMITH');
  assert.strictEqual(result.first, 'John');
  assert.strictEqual(result.last, 'Smith');
});

test('normalizeMoney', () => {
  assert.strictEqual(normalizeMoney('$1,500.00'), '1500.00');
  assert.strictEqual(normalizeMoney('2500'), '2500.00');
  assert.strictEqual(normalizeMoney(''), '');
});

test('normalizeRecord - basic fields', () => {
  const raw = {
    'Booking Number': '2025-001234',
    'Name': 'SMITH, JOHN',
    'DOB': '1990-05-15',
    'Bond': '$1,500.00',
    'Charges': 'DUI - 1st Offense'
  };

  const record = normalizeRecord(raw, 'COLLIER', 'https://example.com');
  
  assert.strictEqual(record.booking_id, '2025-001234');
  assert.strictEqual(record.first_name, 'John');
  assert.strictEqual(record.last_name, 'Smith');
  assert.strictEqual(record.dob, '1990-05-15');
  assert.strictEqual(record.total_bond, '1500.00');
  assert.strictEqual(record.county, 'COLLIER');
  assert.strictEqual(record.charges_raw, 'DUI - 1st Offense');
});

test('qualification scoring - high bond + serious charge', () => {
  const raw = {
    'Booking Number': '2025-001234',
    'Name': 'SMITH, JOHN',
    'Bond': '$2,500.00',
    'Charges': 'Battery - Domestic Violence',
    'Arrest Date': new Date().toISOString() // Today
  };

  const record = normalizeRecord(raw, 'COLLIER', 'https://example.com');
  
  // Should get: +30 (bond >= 500) + 20 (serious charge) + 20 (recent)= 70+
  assert.ok(record.qualified_score >= 70, `Score was ${record.qualified_score}, expected >= 70`);
  assert.strictEqual(record.is_qualified, true);
});
