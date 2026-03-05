import { useState, useRef, useEffect } from 'react';
import './MultiSelect.css';

export default function MultiSelect({ options, selected, onChange, label }) {
    const [isOpen, setIsOpen] = useState(false);
    const [search, setSearch] = useState('');
    const containerRef = useRef(null);
    const searchRef = useRef(null);

    // Close dropdown on outside click
    useEffect(() => {
        const handleClick = (e) => {
            if (containerRef.current && !containerRef.current.contains(e.target)) {
                setIsOpen(false);
                setSearch('');
            }
        };
        document.addEventListener('mousedown', handleClick);
        return () => document.removeEventListener('mousedown', handleClick);
    }, []);

    // Focus search when dropdown opens
    useEffect(() => {
        if (isOpen && searchRef.current) {
            searchRef.current.focus();
        }
    }, [isOpen]);

    const toggleOption = (opt) => {
        if (selected.includes(opt)) {
            onChange(selected.filter(s => s !== opt));
        } else {
            onChange([...selected, opt]);
        }
    };

    const removeTag = (opt, e) => {
        e.stopPropagation();
        onChange(selected.filter(s => s !== opt));
    };

    const clearAll = (e) => {
        e.stopPropagation();
        onChange([]);
    };

    const filteredOptions = options.filter(opt =>
        opt.toLowerCase().includes(search.toLowerCase())
    );

    // Unselected options first in dropdown
    const unselectedOptions = filteredOptions.filter(opt => !selected.includes(opt));
    const selectedInDropdown = filteredOptions.filter(opt => selected.includes(opt));

    return (
        <div className="ms-container" ref={containerRef}>
            {/* Selected tags area + input */}
            <div className="ms-input-area" onClick={() => setIsOpen(!isOpen)}>
                <div className="ms-tags-wrapper">
                    {selected.length === 0 && !isOpen && (
                        <span className="ms-placeholder">Choose options</span>
                    )}
                    {selected.map(item => (
                        <span key={item} className="ms-tag">
                            {item}
                            <span className="ms-tag-x" onClick={(e) => removeTag(item, e)}>×</span>
                        </span>
                    ))}
                    {isOpen && (
                        <input
                            ref={searchRef}
                            className="ms-search-input"
                            type="text"
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            onClick={e => e.stopPropagation()}
                            placeholder={selected.length > 0 ? '' : 'Search...'}
                        />
                    )}
                </div>
                <div className="ms-controls">
                    {selected.length > 0 && (
                        <span className="ms-clear" onClick={clearAll} title="Clear all">✕</span>
                    )}
                    <span className={`ms-chevron ${isOpen ? 'open' : ''}`}>▾</span>
                </div>
            </div>

            {/* Dropdown */}
            {isOpen && (
                <div className="ms-dropdown">
                    {unselectedOptions.length === 0 && selectedInDropdown.length === 0 && (
                        <div className="ms-no-results">No options found</div>
                    )}
                    {/* Unselected items */}
                    {unselectedOptions.map(opt => (
                        <div
                            key={opt}
                            className="ms-option"
                            onClick={() => toggleOption(opt)}
                        >
                            {opt}
                        </div>
                    ))}
                    {/* Selected items shown at bottom with highlight */}
                    {selectedInDropdown.map(opt => (
                        <div
                            key={opt}
                            className="ms-option ms-option-selected"
                            onClick={() => toggleOption(opt)}
                        >
                            {opt}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
