export default function CampoFormulario({ id, etiqueta, ...propsInput }) {
  return (
    <div className="campo">
      <label htmlFor={id}>{etiqueta}</label>
      <input id={id} {...propsInput} />
    </div>
  );
}
// Este es un componente que sera igual para todos los formularios de la app y propsInput nos ayuda a pasarle 
// las propiedades que queramos al input, como el tipo, el placeholder, el valor, etc.